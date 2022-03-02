using UnityEngine.UI;
using System.Collections.Generic;
using UnityEngine;
using System;


public class SpriteController : MonoBehaviour
{
    private bool movementType;
    private bool shownOnScreen;

    // Start is called before the first frame update
    void Start()
    {
        this.gameObject.SetActive(false);

        EventManager.Instance.onUpdatedMotion.AddListener(DoMotion);
        EventManager.Instance.onUpdateMovementType.AddListener(DoMotionTypeSelection);
        EventManager.Instance.onUpdateScreensOn.AddListener(DoScreensSelection);
        EventManager.Instance.onUpdateOpacity.AddListener(DoOpacitySelection);

        movementType = true; // That means rotation
        shownOnScreen = false;
    }

    void DoMotionTypeSelection(string _movementType)
    {
        Debug.Log("Motion Type Selection has happened");
        if (_movementType == "True")
        {
            movementType = true;
        }
        else
        {
            movementType = false;
        }
    }

    void DoScreensSelection(string screens)
    {
        Debug.Log(string.Format("Screens for {0} are set to {1}", transform.name, screens));
        if (transform.name.Contains("Right") && (screens == "Both" || screens == "Right"))
        {
            shownOnScreen = true;
        }
        if (transform.name.Contains("Front") && (screens == "Both" || screens == "Front"))
        {
            shownOnScreen = true;
        }

        //if (transform.name.Contains("Cue"))
        //{
        //    EventManager.Instance.onCueAnimate.Invoke();
        //}
    }

    void DoOpacitySelection(string _opacity)
    {
        float opacity = float.Parse(_opacity);
        if (transform.name.Contains("Target") || transform.name.Contains("Trap"))
        {
            Color current_color = transform.GetComponent<Image>().color;
            transform.GetComponent<Image>().color = new Color(current_color.r, current_color.g, current_color.b, opacity);
        }
    }

    List<int> GetAllSpritesStates(string sprites_message)
    {
        string[] sprites_messages = sprites_message.Split(',');
        List<int> sprites_states = new List<int>();
        foreach (string sm in sprites_messages)
        {
            int state = int.Parse(sm.Substring(sm.IndexOf("=")).Substring(1));
            sprites_states.Add(state);
            //Debug.Log(string.Format("{0} || {1}", sm, sprites_states.Last()));
        }

        return sprites_states;
    }

    int GetStateForThisSprite(List<int> sprites_states)
    {
        int sprite_type = new int();

        if (transform.name.Contains("Cue")) sprite_type = 0;
        if (transform.name.Contains("Manipulandum")) sprite_type = 1;
        if (transform.name.Contains("Target")) sprite_type = 2;
        if (transform.name.Contains("Trap")) sprite_type = 3;

        return sprites_states[sprite_type];
    }

    void HideOrShow(int state)
    {
        this.gameObject.SetActive(false);
        Debug.Log(string.Format("{0} is {1} and screen is {2}", transform.name, state, shownOnScreen));
        if (state != 0 && shownOnScreen)
        {
            this.gameObject.SetActive(true);
            Debug.Log(string.Format("{0} is made Active", transform.name));
        }
    }

    void DoAnimationIfCue(int state)
    {
        //If the sprite is the Cue and it is shown on screen and the state sent by the Heron node is 1 then animate it (that means that states != 1 will not do anything except 0 which will hide it)
        //Debug.Log(state);
        if (transform.name.Contains("Cue") && shownOnScreen && state == 1)
        {
            Debug.Log("Anim invoked");
            if (transform.name.Contains("Right"))
                EventManager.Instance.onCueAnimate.Invoke("Right");
            if (transform.name.Contains("Front"))
                EventManager.Instance.onCueAnimate.Invoke("Front");
        }
    }

    void ChangeTransformIfNotCue(int state)
    {
        if (!transform.name.Contains("Cue") && shownOnScreen)
        {
            if (movementType)
            {
                if (transform.name.Contains("Right"))
                {
                    state += 90;
                }
                transform.rotation = Quaternion.Euler(Vector3.forward * state);
            }
            else
            {
                float step = 2.3f;
                int starting_position = 0;
                if (transform.name.Contains("Right"))
                {
                    transform.rotation = Quaternion.Euler(Vector3.forward * 90);
                    starting_position = 120;
                    transform.position = new Vector3(transform.position.x, starting_position + (int)(step * state), transform.position.z);
                }
                else
                {
                    starting_position = 600;
                    transform.position = new Vector3(starting_position + (int)(step * state), transform.position.y, transform.position.z);
                }

            }


        }
    }

    void DoMotion(string sprites_message)
    {
        List<int> sprites_states = GetAllSpritesStates(sprites_message);

        int state = GetStateForThisSprite(sprites_states);

        ChangeTransformIfNotCue(state);

        HideOrShow(state);

        DoAnimationIfCue(state);

    }
}
