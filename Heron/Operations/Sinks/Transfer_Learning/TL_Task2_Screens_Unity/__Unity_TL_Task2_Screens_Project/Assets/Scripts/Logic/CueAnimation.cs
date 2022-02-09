using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CueAnimation : MonoBehaviour
{
    private string state;
    public float speed;

    void Start()
    {
        state = "still";
        EventManager.Instance.onCueAnimate.AddListener(Loom);
    }

    private void Update()
    {
        if (state == "loom")
        {
            float new_scale = 0.1f + speed * Time.deltaTime;
            if (new_scale > 1.0f)
            {
                new_scale = 1.0f;
                state = "still";
            }
            transform.localScale = new Vector3(new_scale, new_scale, 1.0f);
        }
    }

    void Loom()
    {
        transform.localScale = new Vector3(0.1f, 0.1f, 1.0f);
        state = "loom";
    }
}
