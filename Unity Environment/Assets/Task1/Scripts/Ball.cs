using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using MLAgents;

public class Ball : MonoBehaviour
{
public AudioClip bounceSound;     // needs changing to different source
public AudioSource audioSource;
Agent Task1Agent;
int handCount;
Rigidbody rigidBody;
GameObject body;
// Start is called before the first frame update
void Awake()
{
        audioSource = this.gameObject.GetComponent<AudioSource>();
        audioSource.clip = bounceSound;
        rigidBody = this.gameObject.GetComponent<Rigidbody>();
        rigidBody.maxDepenetrationVelocity = 1000f;
        handCount = 0;
        body = GameObject.Find("Body");
        // Task1Agent = GameObject.Find("Task1Agent").GetComponent<Task1Agent>();
        // Task1Agent = this.transform.parent.gameObject.GetComponent<Task1Agent>();
}

void Start()
{
        Task1Agent = this.transform.parent.gameObject.GetComponent<Task1Agent>();
}

// Update is called once per frame
void FixedUpdate()
{
        if(Vector3.Distance(rigidBody.transform.localPosition, new Vector3(0, 0, 0)) > 5f) {
                Task1Agent.SetReward(-1f);
                Task1Agent.Done();
        }
        // Task1Agent.SetReward(0.00001f*(1/Vector3.Distance(rigidBody.transform.localPosition, body.transform.localPosition)));
}
//Reward assignment is called from the collision of each ball
void OnCollisionEnter( Collision collision){
        //audioSource.Play();
        //rigidBody.useGravity = true;
        if(collision.gameObject.name == "Ground" || collision.gameObject.name == "Body") {
                handCount = 0;
                Task1Agent.SetReward(-1f);
                Task1Agent.Done();
        }
        else if(collision.gameObject.name == "LeftHand" || collision.gameObject.name == "RightHand")
        {
                if(handCount > 0)
                {
                        handCount = 0;
                        Task1Agent.SetReward(-1f);
                        Task1Agent.Done();
                }
                else
                {
                        Task1Agent.SetReward(2f);
                }
        }
        else if(collision.gameObject.name == "Net" && handCount > 0) {
                handCount = 0;
                Task1Agent.SetReward(2f);
                Task1Agent.Done();
        }
}

void OnCollisionStay( Collision collision){
        if(collision.gameObject.name == "Ground" || collision.gameObject.name == "Body") {
                handCount = 0;
                Task1Agent.SetReward(-1f);
                Task1Agent.Done();
        }
        else if(collision.gameObject.name == "Net" && handCount > 0)
        {
                handCount = 0;
                Task1Agent.SetReward(2f);
                Task1Agent.Done();
        }
        else{
                handCount = 0;
                Task1Agent.SetReward(-1f);
                Task1Agent.Done();
        }
}

}
