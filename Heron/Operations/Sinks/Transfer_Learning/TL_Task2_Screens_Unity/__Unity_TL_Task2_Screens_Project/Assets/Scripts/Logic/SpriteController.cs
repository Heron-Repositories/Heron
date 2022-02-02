using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SpriteController: MonoBehaviour
{
    private bool movementType;

    // Start is called before the first frame update
    void Start()
    {
        this.gameObject.SetActive(false);

        EventManager.Instance.onUpdatedMotion.AddListener(DoMotion);
        EventManager.Instance.onUpdateMovementType.AddListener(DoMotionTypeSelection);
        EventManager.Instance.onUpdateScreensOn.AddListener(DoScreensSelection);

        movementType = true; // That means rotation
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
        }
        if (transform.name.Contains("Top") && (screens == "Both" || screens == "Top"))
        {
            this.gameObject.SetActive(true);
        }
    }

    void DoMotion(string coordinates)
    {
        int motion;
        motion = int.Parse(coordinates);
        if (movementType)
            transform.rotation = Quaternion.Euler(Vector3.forward * motion);
        else
            transform.Translate(new Vector3((-1200 / 90 * motion) + 50, transform.position.y, transform.position.z));

    }
}
