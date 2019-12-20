using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using MLAgents;

public class Task1AgentSolo : Agent
{
public GameObject prefab;
// public GameObject LeftHand;
public GameObject RightHand;
//ublic GameObject Torso;
GameObject ball;
public Vector3 startPosition = new Vector3(1.0f, 0.7f, -1.0f);
// public Vector3 leftStart = new Vector3(-0.5f, 1f, 0f);
public Vector3 rightStart = new Vector3(0.5f, 1f, 0f);
public Vector3 torsoStart = new Vector3(0f, 0.75f, -0.5f);
Vector3 origin = new Vector3(0f, 0f, 0f);

void Awake()
{
        RightHand.transform.SetParent(this.transform);
        //Torso.transform.SetParent(this.transform);
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
        ball.transform.localPosition = new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f));
        // ball = Instantiate(prefab, transform.TransformPoint(startPosition + new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f))), Quaternion.identity);
        // ball = Instantiate(prefab, startPosition + new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f)), Quaternion.identity);
        // ball.transform.SetParent(this.transform);
        ball.gameObject.GetComponent<Rigidbody>().velocity = new Vector3(Random.Range(-0.7f, 0.7f), Random.Range(2.0f, 4.0f), Random.Range(-0.7f, 0.7f));
        // LeftHand.gameObject.GetComponent<Rigidbody>().velocity = Vector3.zero;
        RightHand.gameObject.GetComponent<Rigidbody>().velocity = Vector3.zero;
        //Torso.gameObject.GetComponent<Rigidbody>().velocity = Vector3.zero;
        // LeftHand.gameObject.GetComponent<Rigidbody>().transform.localPosition = leftStart;
        RightHand.gameObject.GetComponent<Rigidbody>().transform.localPosition = rightStart;
        //Torso.gameObject.GetComponent<Rigidbody>().transform.localPosition = torsoStart;
        // LeftHand.gameObject.GetComponent<Rigidbody>().transform.localRotation = Quaternion.identity;
        RightHand.gameObject.GetComponent<Rigidbody>().transform.localRotation = Quaternion.identity;
}

public override void CollectObservations()
{
        AddVectorObs(ball.gameObject.GetComponent<Rigidbody>().transform.localPosition);
        AddVectorObs(ball.gameObject.GetComponent<Rigidbody>().velocity);
        // AddVectorObs(LeftHand.gameObject.GetComponent<Rigidbody>().transform.localPosition);
        AddVectorObs(RightHand.gameObject.GetComponent<Rigidbody>().transform.localPosition);
        //AddVectorObs(Torso.gameObject.GetComponent<Rigidbody>().transform.localPosition);
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
        Vector3 rightAcc = Vector3.zero;
        Vector3 torsoAcc = Vector3.zero;
        //Angular control of hands
        // Vector3 leftAng = Vector3.zero;
        Vector3 rightAng = Vector3.zero;

        // leftAcc.x = Mathf.Clamp(vectorAction[0], -100f, 100f);
        // leftAcc.y = Mathf.Clamp(vectorAction[1], -100f, 100f);
        // leftAcc.z = Mathf.Clamp(vectorAction[2], -100f, 100f);
        rightAcc.x = Mathf.Clamp(vectorAction[0], -100f, 100f);
        rightAcc.y = Mathf.Clamp(vectorAction[1], -100f, 100f);
        rightAcc.z = Mathf.Clamp(vectorAction[2], -100f, 100f);
        //  torsoAcc.x = Mathf.Clamp(vectorAction[3], -100f, 100f);
        //  torsoAcc.y = Mathf.Clamp(vectorAction[4], -100f, 100f);
        //  torsoAcc.z = Mathf.Clamp(vectorAction[5], -100f, 100f);
        // leftAng.x = Mathf.Clamp(vectorAction[9], -100f, 100f);
        // leftAng.y = Mathf.Clamp(vectorAction[10], -100f, 100f);
        // leftAng.z = Mathf.Clamp(vectorAction[11], -100f, 100f);
        rightAng.x = Mathf.Clamp(vectorAction[3], -100f, 100f);
        rightAng.y = Mathf.Clamp(vectorAction[4], -100f, 100f);
        rightAng.z = Mathf.Clamp(vectorAction[5], -100f, 100f);
        // LeftHand.gameObject.GetComponent<Rigidbody>().AddForce(leftAcc);
        RightHand.gameObject.GetComponent<Rigidbody>().AddForce(rightAcc);
        // LeftHand.gameObject.GetComponent<Rigidbody>().AddTorque(leftAng);
        RightHand.gameObject.GetComponent<Rigidbody>().AddTorque(rightAng);
        //Torso.gameObject.GetComponent<Rigidbody>().AddForce(torsoAcc * 200f);
}


}
