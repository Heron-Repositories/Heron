using UnityEngine;
using UnityEngine.Events;


public class EventManager : MonoBehaviour
{
    public static EventManager Instance;

    public UnityEvent onStartClient;
    public UnityEvent onClientStarted;
    public UnityEvent onStopClient;
    public UnityEvent onClientStopped;
    public UnityEvent onCueAnimate;

    [System.Serializable]
    public class InteractableObjectEvent : UnityEvent<string> { }

    public InteractableObjectEvent onUpdatedMotion;
    public InteractableObjectEvent onUpdateMovementType;
    public InteractableObjectEvent onUpdateScreensOn;


    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            
            onStartClient = new UnityEvent();
            onClientStarted = new UnityEvent();
            onStopClient = new UnityEvent();
            onClientStopped = new UnityEvent();
            onCueAnimate = new UnityEvent();

            
            onUpdatedMotion = new InteractableObjectEvent();
            onUpdateMovementType = new InteractableObjectEvent();
            onUpdateScreensOn = new InteractableObjectEvent();

        }

        else
            Destroy(this);
    }

}
