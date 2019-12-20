using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TorsoMovement : MonoBehaviour
{
    public GameObject HMD;
    Rigidbody torso;
    // Start is called before the first frame update
    void Start()
    {
      torso = this.gameObject.GetComponent<Rigidbody>();
    }

    // Update is called once per frame
    void FixedUpdate()
    {
        // torso.MovePosition(HMD.transform.position);
    }
}
