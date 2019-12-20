using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RoundnetBall : MonoBehaviour
{
// Start is called before the first frame update
public GameObject prefab;
GameObject ball;
public Vector3 startPosition = new Vector3(1.0f, 0.7f, -1.0f);
Vector3 origin = new Vector3(0f, 0f, 0f);
void Awake(){
        ball = Instantiate(prefab, startPosition, Quaternion.identity);
}
void Start()
{

}

// Update is called once per frame
void FixedUpdate()
{
        // if(ball.transform.position.y <= 0.09702085f){
        //   Destroy(ball);
        //   ball = Instantiate(prefab, startPosition + new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f)), Quaternion.identity);
        //   ball.gameObject.GetComponent<Rigidbody>().velocity = new Vector3(Random.Range(-0.7f, 0.7f), Random.Range(2.0f, 4.0f), Random.Range(-0.7f, 0.7f));
        // }
        // if(Vector3.Distance(ball.transform.position, origin) > 5f){
        //   Destroy(ball);
        //   ball = Instantiate(prefab, startPosition + new Vector3(Random.Range(-0.5f, 0.5f), 0.2f, Random.Range(-0.5f, 0.5f)), Quaternion.identity);
        //   ball.gameObject.GetComponent<Rigidbody>().velocity = new Vector3(Random.Range(-0.70f, 0.7f), Random.Range(2.0f, 4.0f), Random.Range(-0.7f, 0.7f));
        // }

}



}
