import unittest.mock as mock
import pytest

import numpy as np
from mlagents.tf_utils import tf

import yaml

from mlagents.trainers.ppo.models import PPOModel
from mlagents.trainers.ppo.trainer import PPOTrainer, discount_rewards
from mlagents.trainers.ppo.policy import PPOPolicy
from mlagents.trainers.brain import BrainParameters
from mlagents_envs.environment import UnityEnvironment
from mlagents_envs.mock_communicator import MockCommunicator
from mlagents.trainers.tests import mock_brain as mb
from mlagents.trainers.tests.mock_brain import make_brain_parameters
from mlagents.trainers.tests.test_trajectory import make_fake_trajectory
from mlagents.trainers.brain_conversion_utils import (
    step_result_to_brain_info,
    group_spec_to_brain_parameters,
)


@pytest.fixture
def dummy_config():
    return yaml.safe_load(
        """
        trainer: ppo
        batch_size: 32
        beta: 5.0e-3
        buffer_size: 512
        epsilon: 0.2
        hidden_units: 128
        lambd: 0.95
        learning_rate: 3.0e-4
        max_steps: 5.0e4
        normalize: true
        num_epoch: 5
        num_layers: 2
        time_horizon: 64
        sequence_length: 64
        summary_freq: 1000
        use_recurrent: false
        normalize: true
        memory_size: 8
        curiosity_strength: 0.0
        curiosity_enc_size: 1
        summary_path: test
        model_path: test
        reward_signals:
          extrinsic:
            strength: 1.0
            gamma: 0.99
        """
    )


VECTOR_ACTION_SPACE = [2]
VECTOR_OBS_SPACE = 8
DISCRETE_ACTION_SPACE = [3, 3, 3, 2]
BUFFER_INIT_SAMPLES = 32
NUM_AGENTS = 12


@mock.patch("mlagents_envs.environment.UnityEnvironment.executable_launcher")
@mock.patch("mlagents_envs.environment.UnityEnvironment.get_communicator")
def test_ppo_policy_evaluate(mock_communicator, mock_launcher, dummy_config):
    tf.reset_default_graph()
    mock_communicator.return_value = MockCommunicator(
        discrete_action=False, visual_inputs=0
    )
    env = UnityEnvironment(" ")
    env.reset()
    brain_name = env.get_agent_groups()[0]
    brain_info = step_result_to_brain_info(
        env.get_step_result(brain_name), env.get_agent_group_spec(brain_name)
    )
    brain_params = group_spec_to_brain_parameters(
        brain_name, env.get_agent_group_spec(brain_name)
    )

    trainer_parameters = dummy_config
    model_path = brain_name
    trainer_parameters["model_path"] = model_path
    trainer_parameters["keep_checkpoints"] = 3
    policy = PPOPolicy(0, brain_params, trainer_parameters, False, False)
    run_out = policy.evaluate(brain_info)
    assert run_out["action"].shape == (3, 2)
    env.close()


@mock.patch("mlagents_envs.environment.UnityEnvironment.executable_launcher")
@mock.patch("mlagents_envs.environment.UnityEnvironment.get_communicator")
def test_ppo_get_value_estimates(mock_communicator, mock_launcher, dummy_config):
    tf.reset_default_graph()

    brain_params = BrainParameters(
        brain_name="test_brain",
        vector_observation_space_size=1,
        camera_resolutions=[],
        vector_action_space_size=[2],
        vector_action_descriptions=[],
        vector_action_space_type=0,
    )
    dummy_config["summary_path"] = "./summaries/test_trainer_summary"
    dummy_config["model_path"] = "./models/test_trainer_models/TestModel"
    policy = PPOPolicy(0, brain_params, dummy_config, False, False)
    time_horizon = 15
    trajectory = make_fake_trajectory(
        length=time_horizon,
        max_step_complete=True,
        vec_obs_size=1,
        num_vis_obs=0,
        action_space=2,
    )
    run_out = policy.get_value_estimates(trajectory.next_obs, "test_agent", done=False)
    for key, val in run_out.items():
        assert type(key) is str
        assert type(val) is float

    run_out = policy.get_value_estimates(trajectory.next_obs, "test_agent", done=True)
    for key, val in run_out.items():
        assert type(key) is str
        assert val == 0.0

    # Check if we ignore terminal states properly
    policy.reward_signals["extrinsic"].use_terminal_states = False
    run_out = policy.get_value_estimates(trajectory.next_obs, "test_agent", done=True)
    for key, val in run_out.items():
        assert type(key) is str
        assert val != 0.0

    agentbuffer = trajectory.to_agentbuffer()
    batched_values = policy.get_batched_value_estimates(agentbuffer)
    for values in batched_values.values():
        assert len(values) == 15


def test_ppo_model_cc_vector():
    tf.reset_default_graph()
    with tf.Session() as sess:
        with tf.variable_scope("FakeGraphScope"):
            model = PPOModel(
                make_brain_parameters(discrete_action=False, visual_inputs=0)
            )
            init = tf.global_variables_initializer()
            sess.run(init)

            run_list = [
                model.output,
                model.log_probs,
                model.value,
                model.entropy,
                model.learning_rate,
            ]
            feed_dict = {
                model.batch_size: 2,
                model.sequence_length: 1,
                model.vector_in: np.array([[1, 2, 3, 1, 2, 3], [3, 4, 5, 3, 4, 5]]),
                model.epsilon: np.array([[0, 1], [2, 3]]),
            }
            sess.run(run_list, feed_dict=feed_dict)


def test_ppo_model_cc_visual():
    tf.reset_default_graph()
    with tf.Session() as sess:
        with tf.variable_scope("FakeGraphScope"):
            model = PPOModel(
                make_brain_parameters(discrete_action=False, visual_inputs=2)
            )
            init = tf.global_variables_initializer()
            sess.run(init)

            run_list = [
                model.output,
                model.log_probs,
                model.value,
                model.entropy,
                model.learning_rate,
            ]
            feed_dict = {
                model.batch_size: 2,
                model.sequence_length: 1,
                model.vector_in: np.array([[1, 2, 3, 1, 2, 3], [3, 4, 5, 3, 4, 5]]),
                model.visual_in[0]: np.ones([2, 40, 30, 3], dtype=np.float32),
                model.visual_in[1]: np.ones([2, 40, 30, 3], dtype=np.float32),
                model.epsilon: np.array([[0, 1], [2, 3]], dtype=np.float32),
            }
            sess.run(run_list, feed_dict=feed_dict)


def test_ppo_model_dc_visual():
    tf.reset_default_graph()
    with tf.Session() as sess:
        with tf.variable_scope("FakeGraphScope"):
            model = PPOModel(
                make_brain_parameters(discrete_action=True, visual_inputs=2)
            )
            init = tf.global_variables_initializer()
            sess.run(init)

            run_list = [
                model.output,
                model.all_log_probs,
                model.value,
                model.entropy,
                model.learning_rate,
            ]
            feed_dict = {
                model.batch_size: 2,
                model.sequence_length: 1,
                model.vector_in: np.array([[1, 2, 3, 1, 2, 3], [3, 4, 5, 3, 4, 5]]),
                model.visual_in[0]: np.ones([2, 40, 30, 3], dtype=np.float32),
                model.visual_in[1]: np.ones([2, 40, 30, 3], dtype=np.float32),
                model.action_masks: np.ones([2, 2], dtype=np.float32),
            }
            sess.run(run_list, feed_dict=feed_dict)


def test_ppo_model_dc_vector():
    tf.reset_default_graph()
    with tf.Session() as sess:
        with tf.variable_scope("FakeGraphScope"):
            model = PPOModel(
                make_brain_parameters(discrete_action=True, visual_inputs=0)
            )
            init = tf.global_variables_initializer()
            sess.run(init)

            run_list = [
                model.output,
                model.all_log_probs,
                model.value,
                model.entropy,
                model.learning_rate,
            ]
            feed_dict = {
                model.batch_size: 2,
                model.sequence_length: 1,
                model.vector_in: np.array([[1, 2, 3, 1, 2, 3], [3, 4, 5, 3, 4, 5]]),
                model.action_masks: np.ones([2, 2], dtype=np.float32),
            }
            sess.run(run_list, feed_dict=feed_dict)


def test_ppo_model_dc_vector_rnn():
    tf.reset_default_graph()
    with tf.Session() as sess:
        with tf.variable_scope("FakeGraphScope"):
            memory_size = 128
            model = PPOModel(
                make_brain_parameters(discrete_action=True, visual_inputs=0),
                use_recurrent=True,
                m_size=memory_size,
            )
            init = tf.global_variables_initializer()
            sess.run(init)

            run_list = [
                model.output,
                model.all_log_probs,
                model.value,
                model.entropy,
                model.learning_rate,
                model.memory_out,
            ]
            feed_dict = {
                model.batch_size: 1,
                model.sequence_length: 2,
                model.prev_action: [[0], [0]],
                model.memory_in: np.zeros((1, memory_size), dtype=np.float32),
                model.vector_in: np.array([[1, 2, 3, 1, 2, 3], [3, 4, 5, 3, 4, 5]]),
                model.action_masks: np.ones([1, 2], dtype=np.float32),
            }
            sess.run(run_list, feed_dict=feed_dict)


def test_ppo_model_cc_vector_rnn():
    tf.reset_default_graph()
    with tf.Session() as sess:
        with tf.variable_scope("FakeGraphScope"):
            memory_size = 128
            model = PPOModel(
                make_brain_parameters(discrete_action=False, visual_inputs=0),
                use_recurrent=True,
                m_size=memory_size,
            )
            init = tf.global_variables_initializer()
            sess.run(init)

            run_list = [
                model.output,
                model.all_log_probs,
                model.value,
                model.entropy,
                model.learning_rate,
                model.memory_out,
            ]
            feed_dict = {
                model.batch_size: 1,
                model.sequence_length: 2,
                model.memory_in: np.zeros((1, memory_size), dtype=np.float32),
                model.vector_in: np.array([[1, 2, 3, 1, 2, 3], [3, 4, 5, 3, 4, 5]]),
                model.epsilon: np.array([[0, 1]]),
            }
            sess.run(run_list, feed_dict=feed_dict)


def test_rl_functions():
    rewards = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    gamma = 0.9
    returns = discount_rewards(rewards, gamma, 0.0)
    np.testing.assert_array_almost_equal(
        returns, np.array([0.729, 0.81, 0.9, 1.0], dtype=np.float32)
    )


def test_trainer_increment_step(dummy_config):
    trainer_params = dummy_config
    brain_params = BrainParameters(
        brain_name="test_brain",
        vector_observation_space_size=1,
        camera_resolutions=[],
        vector_action_space_size=[2],
        vector_action_descriptions=[],
        vector_action_space_type=0,
    )

    trainer = PPOTrainer(brain_params, 0, trainer_params, True, False, 0, "0", False)
    policy_mock = mock.Mock()
    step_count = 10
    policy_mock.increment_step = mock.Mock(return_value=step_count)
    trainer.policy = policy_mock

    trainer.increment_step(5)
    policy_mock.increment_step.assert_called_with(5)
    assert trainer.step == 10


@mock.patch("mlagents_envs.environment.UnityEnvironment")
@pytest.mark.parametrize("use_discrete", [True, False])
def test_trainer_update_policy(mock_env, dummy_config, use_discrete):
    env, mock_brain, _ = mb.setup_mock_env_and_brains(
        mock_env,
        use_discrete,
        False,
        num_agents=NUM_AGENTS,
        vector_action_space=VECTOR_ACTION_SPACE,
        vector_obs_space=VECTOR_OBS_SPACE,
        discrete_action_space=DISCRETE_ACTION_SPACE,
    )

    trainer_params = dummy_config
    trainer_params["use_recurrent"] = True

    # Test curiosity reward signal
    trainer_params["reward_signals"]["curiosity"] = {}
    trainer_params["reward_signals"]["curiosity"]["strength"] = 1.0
    trainer_params["reward_signals"]["curiosity"]["gamma"] = 0.99
    trainer_params["reward_signals"]["curiosity"]["encoding_size"] = 128

    trainer = PPOTrainer(mock_brain, 0, trainer_params, True, False, 0, "0", False)
    # Test update with sequence length smaller than batch size
    buffer = mb.simulate_rollout(env, trainer.policy, BUFFER_INIT_SAMPLES)
    # Mock out reward signal eval
    buffer["extrinsic_rewards"] = buffer["rewards"]
    buffer["extrinsic_returns"] = buffer["rewards"]
    buffer["extrinsic_value_estimates"] = buffer["rewards"]
    buffer["curiosity_rewards"] = buffer["rewards"]
    buffer["curiosity_returns"] = buffer["rewards"]
    buffer["curiosity_value_estimates"] = buffer["rewards"]

    trainer.update_buffer = buffer
    trainer.update_policy()
    # Make batch length a larger multiple of sequence length
    trainer.trainer_parameters["batch_size"] = 128
    trainer.update_policy()
    # Make batch length a larger non-multiple of sequence length
    trainer.trainer_parameters["batch_size"] = 100
    trainer.update_policy()


def test_process_trajectory(dummy_config):
    brain_params = BrainParameters(
        brain_name="test_brain",
        vector_observation_space_size=1,
        camera_resolutions=[],
        vector_action_space_size=[2],
        vector_action_descriptions=[],
        vector_action_space_type=0,
    )
    dummy_config["summary_path"] = "./summaries/test_trainer_summary"
    dummy_config["model_path"] = "./models/test_trainer_models/TestModel"
    trainer = PPOTrainer(brain_params, 0, dummy_config, True, False, 0, "0", False)
    time_horizon = 15
    trajectory = make_fake_trajectory(
        length=time_horizon,
        max_step_complete=True,
        vec_obs_size=1,
        num_vis_obs=0,
        action_space=2,
    )
    trainer.process_trajectory(trajectory)

    # Check that trainer put trajectory in update buffer
    assert trainer.update_buffer.num_experiences == 15

    # Check that GAE worked
    assert (
        "advantages" in trainer.update_buffer
        and "discounted_returns" in trainer.update_buffer
    )

    # Check that the stats are being collected as episode isn't complete
    for reward in trainer.collected_rewards.values():
        for agent in reward.values():
            assert agent > 0

    # Add a terminal trajectory
    trajectory = make_fake_trajectory(
        length=time_horizon + 1,
        max_step_complete=False,
        vec_obs_size=1,
        num_vis_obs=0,
        action_space=2,
    )
    trainer.process_trajectory(trajectory)

    # Check that the stats are reset as episode is finished
    for reward in trainer.collected_rewards.values():
        for agent in reward.values():
            assert agent == 0
    assert trainer.stats_reporter.get_stats_summaries("Policy/Extrinsic Reward").num > 0


def test_normalization(dummy_config):
    brain_params = BrainParameters(
        brain_name="test_brain",
        vector_observation_space_size=1,
        camera_resolutions=[],
        vector_action_space_size=[2],
        vector_action_descriptions=[],
        vector_action_space_type=0,
    )
    dummy_config["summary_path"] = "./summaries/test_trainer_summary"
    dummy_config["model_path"] = "./models/test_trainer_models/TestModel"
    trainer = PPOTrainer(brain_params, 0, dummy_config, True, False, 0, "0", False)
    time_horizon = 6
    trajectory = make_fake_trajectory(
        length=time_horizon,
        max_step_complete=True,
        vec_obs_size=1,
        num_vis_obs=0,
        action_space=2,
    )
    # Change half of the obs to 0
    for i in range(3):
        trajectory.steps[i].obs[0] = np.zeros(1, dtype=np.float32)
    trainer.process_trajectory(trajectory)

    # Check that the running mean and variance is correct
    steps, mean, variance = trainer.ppo_policy.sess.run(
        [
            trainer.policy.model.normalization_steps,
            trainer.policy.model.running_mean,
            trainer.policy.model.running_variance,
        ]
    )

    assert steps == 6
    assert mean[0] == 0.5
    # Note: variance is divided by number of steps, and initialized to 1 to avoid
    # divide by 0. The right answer is 0.25
    assert (variance[0] - 1) / steps == 0.25

    # Make another update, this time with all 1's
    time_horizon = 10
    trajectory = make_fake_trajectory(
        length=time_horizon,
        max_step_complete=True,
        vec_obs_size=1,
        num_vis_obs=0,
        action_space=2,
    )
    trainer.process_trajectory(trajectory)

    # Check that the running mean and variance is correct
    steps, mean, variance = trainer.ppo_policy.sess.run(
        [
            trainer.policy.model.normalization_steps,
            trainer.policy.model.running_mean,
            trainer.policy.model.running_variance,
        ]
    )

    assert steps == 16
    assert mean[0] == 0.8125
    assert (variance[0] - 1) / steps == pytest.approx(0.152, abs=0.01)


if __name__ == "__main__":
    pytest.main()
