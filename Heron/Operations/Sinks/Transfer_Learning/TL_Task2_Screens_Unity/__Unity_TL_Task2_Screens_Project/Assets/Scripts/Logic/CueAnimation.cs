using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CueAnimation : MonoBehaviour
{
    private string state;
    [SerializeField] public Animator animation;

    void Start()
    {
        EventManager.Instance.onCueAnimate.AddListener(Loom);
    }

    void Loom()
    {
        animation.Play("CueLooming");
    }

 
}
