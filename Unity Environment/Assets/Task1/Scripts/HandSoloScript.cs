using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class HandSoloScript : MonoBehaviour
{
//public GameObject Controller;
public GameObject hand;
public Vector3 offset = new Vector3(0, 0, 0);
// public GameObject torso;
Rigidbody rigid;


// Start is called before the first frame update
void Start()
{
        rigid = hand.gameObject.GetComponent<Rigidbody>();
}

// FixedUpdate is called once per frame
void FixedUpdate()
{
        // rigid.MovePosition(Controller.transform.localPosition);
        // rigid.MoveRotation(Controller.transform.rotation);
        // if(Vector3.Distance(rigid.transform.localPosition, torso.transform.localPosition) >= Vector3.Distance(offset, Vector3.zero))
        // {
        //normal vector to the sphere encasing the body
        // Vector3 direction =  Vector3.Normalize(rigid.transform.localPosition - torso.transform.localPosition);
        // Vector3 normalVector = Vector3.Project(rigid.velocity, direction);
        // rigid.velocity = rigid.velocity - normalVector + torso.gameObject.GetComponent<Rigidbody>().velocity;
        // rigid.transform.localPosition = Vector3.Distance(offset, Vector3.zero) * normalVector;
        // }
        if(Vector3.Distance(rigid.transform.localPosition, Vector3.zero) > 5f)
        {
                Vector3 direction =  Vector3.Normalize(rigid.transform.localPosition - Vector3.zero);
                Vector3 normalVector = Vector3.Project(rigid.velocity, direction);
                rigid.velocity = rigid.velocity - normalVector;
                rigid.transform.localPosition = Vector3.Distance(offset, Vector3.zero) * normalVector;
        }
        rigid.velocity = new Vector3(Mathf.Clamp(rigid.velocity.x, -100f, 100f), Mathf.Clamp(rigid.velocity.y, -100f, 100), Mathf.Clamp(rigid.velocity.z, -100f, 100));
        rigid.transform.localPosition = new Vector3(Mathf.Clamp(rigid.transform.localPosition.x, -100f, 100f), Mathf.Clamp(rigid.transform.localPosition.y, -100f, 100f), Mathf.Clamp(rigid.transform.localPosition.z, -100f, 100f));
}
}
