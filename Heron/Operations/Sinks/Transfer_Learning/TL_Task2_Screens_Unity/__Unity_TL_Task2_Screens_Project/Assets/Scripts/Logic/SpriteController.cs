using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;


public class SpriteController: MonoBehaviour
{
    private bool movementType;
    private bool screenOn;

    // Start is called before the first frame update
    void Start()
    {
        this.gameObject.SetActive(false);

        EventManager.Instance.onUpdatedMotion.AddListener(DoMotion);
        EventManager.Instance.onUpdateMovementType.AddListener(DoMotionTypeSelection);
        EventManager.Instance.onUpdateScreensOn.AddListener(DoScreensSelection);

        movementType = true; // That means rotation
        screenOn = false;
    }

    void DoMotionTypeSelection(string _movementType)
    {
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
        if(transform.name.Contains("Left") && (screens=="Both" || screens== "Left"))
        {
            this.gameObject.SetActive(true);
            screenOn = true;
        }
        if (transform.name.Contains("Front") && (screens == "Both" || screens == "Front"))
        {
            this.gameObject.SetActive(true);
            screenOn = true;
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
        if (state != 0 && screenOn)
        {
            this.gameObject.SetActive(true);
        }
    }

    void DoAnimationIfCue()
    {
        if (transform.name.Contains("Cue") && screenOn)
        {
            EventManager.Instance.onCueAnimate.Invoke();
        }
    }

    void DoMotion(string sprites_message)
    {
        List<int> sprites_states = GetAllSpritesStates(sprites_message);

        int motion = GetStateForThisSprite(sprites_states);

        HideOrShow(motion);



        if (movementType)
            transform.rotation = Quaternion.Euler(Vector3.forward * motion);
        else
            transform.Translate(new Vector3((-1200 / 90 * motion) + 50, transform.position.y, transform.position.z));

    }
}
