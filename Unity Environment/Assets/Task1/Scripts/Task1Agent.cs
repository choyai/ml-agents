using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using MLAgents;

public class Task1Agent : Agent
{
public GameObject prefab;
// public GameObject LeftHand;
public GameObject RightHand;
public GameObject Torso;
GameObject ball;
public Vector3 startPosition = new Vector3(1.0f, 0.7f, -1.0f);
// public Vector3 leftStart = new Vector3(-0.5f, 1f, 0f);
public Vector3 rightStart = new Vector3(0.5f, 1f, 0f);
public Vector3 torsoStart = new Vector3(0f, 0.75f, -0.5f);
Vector3 rightVelocity = Vector3.zero;
Vector3 rightAngVelocity = Vector3.zero;
Vector3 TorsoVelocity = Vector3.zero;
Vector3 rightAcc = Vector3.zero;
Vector3 torsoAcc = Vector3.zero;
Vector3 rightAng = Vector3.zero;
Vector3 origin = new Vector3(0f, 0f, 0f);

void Awake()
{
        RightHand.transform.SetParent(this.transform);
        Torso.transform.SetParent(this.transform);
        ball = Instantiate(prefab, transform.TransformPoint(startPosition), Quaternion.identity);
        ball.transform.SetParent(this.transform);
}

void Start()
{

}

public override void AgentReset()
{
        // Destroy(ball);
        ball.gameObject.GetComponent<Rigidbody>().velocity = Vector3.zero;
        // ball.gameObject.GetComponent<Rigidbody>().acceleration = Vector3.zero;
        ball.gameObject.GetComponent<Rigidbody>().angularVelocity = Vector3.zero;
        // ball.gameObject.GetComponent<Rigidbody>().angularAcceleration = Vector3.zero;
        ball.transform.localPosition = startPosition + new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f));
        // ball = Instantiate(prefab, transform.TransformPoint(startPosition + new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f))), Quaternion.identity);
        // ball = Instantiate(prefab, startPosition + new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f)), Quaternion.identity);
        // ball.transform.SetParent(this.transform);
        ball.gameObject.GetComponent<Rigidbody>().velocity = new Vector3(Random.Range(-0.7f, 0.7f), Random.Range(2.0f, 4.0f), Random.Range(-0.7f, 0.7f));
        // LeftHand.gameObject.GetComponent<Rigidbody>().velocity = Vector3.zero;
        RightHand.gameObject.GetComponent<Rigidbody>().velocity = Vector3.zero;
        Torso.gameObject.GetComponent<Rigidbody>().velocity = Vector3.zero;
        // LeftHand.gameObject.GetComponent<Rigidbody>().transform.localPosition = leftStart;
        RightHand.gameObject.GetComponent<Rigidbody>().transform.localPosition = rightStart;
        Torso.gameObject.GetComponent<Rigidbody>().transform.localPosition = torsoStart;
        // LeftHand.gameObject.GetComponent<Rigidbody>().transform.localRotation = Quaternion.identity;
        RightHand.gameObject.GetComponent<Rigidbody>().transform.localRotation = Quaternion.identity;
}

public override void CollectObservations()
{
        AddVectorObs(ball.gameObject.GetComponent<Rigidbody>().transform.localPosition);
        AddVectorObs(ball.gameObject.GetComponent<Rigidbody>().velocity);
        // AddVectorObs(LeftHand.gameObject.GetComponent<Rigidbody>().transform.localPosition);
        AddVectorObs(RightHand.gameObject.GetComponent<Rigidbody>().transform.localPosition);
        AddVectorObs(Torso.gameObject.GetComponent<Rigidbody>().transform.localPosition);
        // AddVectorObs(LeftHand.gameObject.GetComponent<Rigidbody>().velocity);
        AddVectorObs(RightHand.gameObject.GetComponent<Rigidbody>().velocity);
        // AddVectorObs(LeftHand.gameObject.GetComponent<Rigidbody>().transform.localRotation);
        AddVectorObs(RightHand.gameObject.GetComponent<Rigidbody>().transform.localRotation);
        // AddVectorObs(LeftHand.gameObject.GetComponent<Rigidbody>().angularVelocity);
        AddVectorObs(RightHand.gameObject.GetComponent<Rigidbody>().angularVelocity);
}

public override void AgentAction(float[] vectorAction, string textAction)
{
        //Control of each limb
        // Vector3 leftAcc = Vector3.zero;

        //Angular control of hands
        // Vector3 leftAng = Vector3.zero;


        rightAcc.x = Mathf.Clamp(vectorAction[0], -100f, 100f);
        rightAcc.y = Mathf.Clamp(vectorAction[1], -100f, 100f);
        rightAcc.z = Mathf.Clamp(vectorAction[2], -100f, 100f);
        torsoAcc.x = Mathf.Clamp(vectorAction[3], -100f, 100f);
        torsoAcc.y = Mathf.Clamp(vectorAction[4], -100f, 100f);
        torsoAcc.z = Mathf.Clamp(vectorAction[5], -100f, 100f);

        rightAng.x = Mathf.Clamp(vectorAction[6], -100f, 100f);
        rightAng.y = Mathf.Clamp(vectorAction[7], -100f, 100f);
        rightAng.z = Mathf.Clamp(vectorAction[8], -100f, 100f);

}

void FixedUpdate(){
  Quaternion delta_rotation = Quaternion.Euler(RightHand.gameObject.transform.rotation.eulerAngles + rightAngVelocity * Time.deltaTime);
  rightVelocity = RightHand.gameObject.GetComponent<Rigidbody>().velocity + rightAcc * Time.deltaTime;
  rightAngVelocity = RightHand.gameObject.GetComponent<Rigidbody>().angularVelocity + rightAng * Time.deltaTime;
  TorsoVelocity = Torso.gameObject.GetComponent<Rigidbody>().velocity + torsoAcc * Time.deltaTime;

  RightHand.gameObject.GetComponent<Rigidbody>().MovePosition(RightHand.gameObject.transform.position + rightVelocity * Time.deltaTime);
  RightHand.gameObject.GetComponent<Rigidbody>().MoveRotation(delta_rotation);
  Torso.gameObject.GetComponent<Rigidbody>().MovePosition(Torso.gameObject.transform.position + TorsoVelocity * Time.deltaTime);
}


}
