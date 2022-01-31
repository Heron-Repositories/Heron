using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Rotation : MonoBehaviour
{

    // Start is called before the first frame update
    void Start()
    {
        EventManager.Instance.onUpdatedMotion.AddListener(DoRotation);
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    void DoRotation(string coordinates)
    {
        int angle;
        //Debug.Log("[" + coordinates + "]");
        angle = int.Parse(coordinates);
        transform.rotation = Quaternion.Euler(Vector3.forward * angle);
    }
}
