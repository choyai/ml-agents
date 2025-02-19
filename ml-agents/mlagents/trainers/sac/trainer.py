# # Unity ML-Agents Toolkit
# ## ML-Agent Learning (SAC)
# Contains an implementation of SAC as described in https://arxiv.org/abs/1801.01290
# and implemented in https://github.com/hill-a/stable-baselines

import logging
from collections import defaultdict
from typing import Dict
import os

import numpy as np

from mlagents_envs.timers import timed
from mlagents.trainers.sac.policy import SACPolicy
from mlagents.trainers.rl_trainer import RLTrainer
from mlagents.trainers.trajectory import Trajectory, SplitObservations


LOGGER = logging.getLogger("mlagents.trainers")
BUFFER_TRUNCATE_PERCENT = 0.8


class SACTrainer(RLTrainer):
    """
    The SACTrainer is an implementation of the SAC algorithm, with support
    for discrete actions and recurrent networks.
    """

    def __init__(
        self, brain, reward_buff_cap, trainer_parameters, training, load, seed, run_id
    ):
        """
        Responsible for collecting experiences and training SAC model.
        :param trainer_parameters: The parameters for the trainer (dictionary).
        :param training: Whether the trainer is set for training.
        :param load: Whether the model should be loaded.
        :param seed: The seed the model will be initialized with
        :param run_id: The The identifier of the current run
        """
        super().__init__(brain, trainer_parameters, training, run_id, reward_buff_cap)
        self.param_keys = [
            "batch_size",
            "buffer_size",
            "buffer_init_steps",
            "hidden_units",
            "learning_rate",
            "init_entcoef",
            "max_steps",
            "normalize",
            "num_update",
            "num_layers",
            "time_horizon",
            "sequence_length",
            "summary_freq",
            "tau",
            "use_recurrent",
            "summary_path",
            "memory_size",
            "model_path",
            "reward_signals",
            "vis_encode_type",
        ]

        self.check_param_keys()

        self.step = 0
        self.train_interval = (
            trainer_parameters["train_interval"]
            if "train_interval" in trainer_parameters
            else 1
        )
        self.reward_signal_updates_per_train = (
            trainer_parameters["reward_signals"]["reward_signal_num_update"]
            if "reward_signal_num_update" in trainer_parameters["reward_signals"]
            else trainer_parameters["num_update"]
        )

        self.checkpoint_replay_buffer = (
            trainer_parameters["save_replay_buffer"]
            if "save_replay_buffer" in trainer_parameters
            else False
        )
        self.sac_policy = SACPolicy(
            seed, brain, trainer_parameters, self.is_training, load
        )
        self.policy = self.sac_policy

        # Load the replay buffer if load
        if load and self.checkpoint_replay_buffer:
            try:
                self.load_replay_buffer()
            except (AttributeError, FileNotFoundError):
                LOGGER.warning(
                    "Replay buffer was unable to load, starting from scratch."
                )
            LOGGER.debug(
                "Loaded update buffer with {} sequences".format(
                    self.update_buffer.num_experiences
                )
            )

        for _reward_signal in self.policy.reward_signals.keys():
            self.collected_rewards[_reward_signal] = defaultdict(lambda: 0)

    def save_model(self) -> None:
        """
        Saves the model. Overrides the default save_model since we want to save
        the replay buffer as well.
        """
        self.policy.save_model(self.get_step)
        if self.checkpoint_replay_buffer:
            self.save_replay_buffer()

    def save_replay_buffer(self) -> None:
        """
        Save the training buffer's update buffer to a pickle file.
        """
        filename = os.path.join(self.policy.model_path, "last_replay_buffer.hdf5")
        LOGGER.info("Saving Experience Replay Buffer to {}".format(filename))
        with open(filename, "wb") as file_object:
            self.update_buffer.save_to_file(file_object)

    def load_replay_buffer(self) -> None:
        """
        Loads the last saved replay buffer from a file.
        """
        filename = os.path.join(self.policy.model_path, "last_replay_buffer.hdf5")
        LOGGER.info("Loading Experience Replay Buffer from {}".format(filename))
        with open(filename, "rb+") as file_object:
            self.update_buffer.load_from_file(file_object)
        LOGGER.info(
            "Experience replay buffer has {} experiences.".format(
                self.update_buffer.num_experiences
            )
        )

    def process_trajectory(self, trajectory: Trajectory) -> None:
        """
        Takes a trajectory and processes it, putting it into the replay buffer.
        """
        last_step = trajectory.steps[-1]
        agent_id = trajectory.agent_id  # All the agents should have the same ID

        # Add to episode_steps
        self.episode_steps[agent_id] += len(trajectory.steps)

        agent_buffer_trajectory = trajectory.to_agentbuffer()

        # Update the normalization
        if self.is_training:
            self.policy.update_normalization(agent_buffer_trajectory["vector_obs"])

        # Evaluate all reward functions for reporting purposes
        self.collected_rewards["environment"][agent_id] += np.sum(
            agent_buffer_trajectory["environment_rewards"]
        )
        for name, reward_signal in self.policy.reward_signals.items():
            evaluate_result = reward_signal.evaluate_batch(
                agent_buffer_trajectory
            ).scaled_reward
            # Report the reward signals
            self.collected_rewards[name][agent_id] += np.sum(evaluate_result)

        # Get all value estimates for reporting purposes
        value_estimates = self.policy.get_batched_value_estimates(
            agent_buffer_trajectory
        )
        for name, v in value_estimates.items():
            self.stats_reporter.add_stat(
                self.policy.reward_signals[name].value_name, np.mean(v)
            )

        # Bootstrap using the last step rather than the bootstrap step if max step is reached.
        # Set last element to duplicate obs and remove dones.
        if last_step.max_step:
            vec_vis_obs = SplitObservations.from_observations(last_step.obs)
            for i, obs in enumerate(vec_vis_obs.visual_observations):
                agent_buffer_trajectory["next_visual_obs%d" % i][-1] = obs
            if vec_vis_obs.vector_observations.size > 1:
                agent_buffer_trajectory["next_vector_in"][
                    -1
                ] = vec_vis_obs.vector_observations
            agent_buffer_trajectory["done"][-1] = False

        # Append to update buffer
        agent_buffer_trajectory.resequence_and_append(
            self.update_buffer, training_length=self.policy.sequence_length
        )

        if trajectory.done_reached:
            self._update_end_episode_stats(agent_id)

    def is_ready_update(self) -> bool:
        """
        Returns whether or not the trainer has enough elements to run update model
        :return: A boolean corresponding to whether or not update_model() can be run
        """
        return (
            self.update_buffer.num_experiences >= self.trainer_parameters["batch_size"]
            and self.step >= self.trainer_parameters["buffer_init_steps"]
        )

    @timed
    def update_policy(self) -> None:
        """
        If train_interval is met, update the SAC policy given the current reward signals.
        If reward_signal_train_interval is met, update the reward signals from the buffer.
        """
        if self.step % self.train_interval == 0:
            self.trainer_metrics.start_policy_update_timer(
                number_experiences=self.update_buffer.num_experiences,
                mean_return=float(np.mean(self.cumulative_returns_since_policy_update)),
            )
            self.update_sac_policy()
            self.update_reward_signals()
            self.trainer_metrics.end_policy_update()

    def update_sac_policy(self) -> None:
        """
        Uses demonstration_buffer to update the policy.
        The reward signal generators are updated using different mini batches.
        If we want to imitate http://arxiv.org/abs/1809.02925 and similar papers, where the policy is updated
        N times, then the reward signals are updated N times, then reward_signal_updates_per_train
        is greater than 1 and the reward signals are not updated in parallel.
        """

        self.cumulative_returns_since_policy_update.clear()
        n_sequences = max(
            int(self.trainer_parameters["batch_size"] / self.policy.sequence_length), 1
        )

        num_updates = self.trainer_parameters["num_update"]
        batch_update_stats: Dict[str, list] = defaultdict(list)
        for _ in range(num_updates):
            LOGGER.debug("Updating SAC policy at step {}".format(self.step))
            buffer = self.update_buffer
            if (
                self.update_buffer.num_experiences
                >= self.trainer_parameters["batch_size"]
            ):
                sampled_minibatch = buffer.sample_mini_batch(
                    self.trainer_parameters["batch_size"],
                    sequence_length=self.policy.sequence_length,
                )
                # Get rewards for each reward
                for name, signal in self.policy.reward_signals.items():
                    sampled_minibatch[
                        "{}_rewards".format(name)
                    ] = signal.evaluate_batch(sampled_minibatch).scaled_reward

                update_stats = self.policy.update(sampled_minibatch, n_sequences)
                for stat_name, value in update_stats.items():
                    batch_update_stats[stat_name].append(value)

        # Truncate update buffer if neccessary. Truncate more than we need to to avoid truncating
        # a large buffer at each update.
        if self.update_buffer.num_experiences > self.trainer_parameters["buffer_size"]:
            self.update_buffer.truncate(
                int(self.trainer_parameters["buffer_size"] * BUFFER_TRUNCATE_PERCENT)
            )

        for stat, stat_list in batch_update_stats.items():
            self.stats_reporter.add_stat(stat, np.mean(stat_list))

        bc_module = self.sac_policy.bc_module
        if bc_module:
            update_stats = bc_module.update()
            for stat, val in update_stats.items():
                self.stats_reporter.add_stat(stat, val)

    def update_reward_signals(self) -> None:
        """
        Iterate through the reward signals and update them. Unlike in PPO,
        do it separate from the policy so that it can be done at a different
        interval.
        This function should only be used to simulate
        http://arxiv.org/abs/1809.02925 and similar papers, where the policy is updated
        N times, then the reward signals are updated N times. Normally, the reward signal
        and policy are updated in parallel.
        """
        buffer = self.update_buffer
        num_updates = self.reward_signal_updates_per_train
        n_sequences = max(
            int(self.trainer_parameters["batch_size"] / self.policy.sequence_length), 1
        )
        batch_update_stats: Dict[str, list] = defaultdict(list)
        for _ in range(num_updates):
            # Get minibatches for reward signal update if needed
            reward_signal_minibatches = {}
            for name, signal in self.policy.reward_signals.items():
                LOGGER.debug("Updating {} at step {}".format(name, self.step))
                # Some signals don't need a minibatch to be sampled - so we don't!
                if signal.update_dict:
                    reward_signal_minibatches[name] = buffer.sample_mini_batch(
                        self.trainer_parameters["batch_size"],
                        sequence_length=self.policy.sequence_length,
                    )
            update_stats = self.sac_policy.update_reward_signals(
                reward_signal_minibatches, n_sequences
            )
            for stat_name, value in update_stats.items():
                batch_update_stats[stat_name].append(value)
        for stat, stat_list in batch_update_stats.items():
            self.stats_reporter.add_stat(stat, np.mean(stat_list))
