using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CueAnimation : MonoBehaviour
{
    [SerializeField] public Animator anim;

    void Start()
    {
        EventManager.Instance.onCueAnimate.AddListener(Loom);
    }

    void Loom(string side)
    {
        anim.Play("CueLooming" + side);
    }

 
}
