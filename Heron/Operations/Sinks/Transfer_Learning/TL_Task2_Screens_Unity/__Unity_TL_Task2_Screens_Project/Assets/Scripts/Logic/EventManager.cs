using UnityEngine;
using UnityEngine.Events;


public class EventManager : MonoBehaviour
{
    public static EventManager Instance;

    public UnityEvent onStartClient;
    public UnityEvent onClientStarted;
    public UnityEvent onStopClient;
    public UnityEvent onClientStopped;

    [System.Serializable]
    public class InteractableObjectEvent : UnityEvent<string> { }

    public InteractableObjectEvent onUpdatedMotion;
    public InteractableObjectEvent onUpdateMovementType;
    public InteractableObjectEvent onUpdateScreensOn;
    public InteractableObjectEvent onUpdateOpacity;
    public InteractableObjectEvent onCueAnimate;


    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            
            onStartClient = new UnityEvent();
            onClientStarted = new UnityEvent();
            onStopClient = new UnityEvent();
            onClientStopped = new UnityEvent();

            
            onUpdatedMotion = new InteractableObjectEvent();
            onUpdateMovementType = new InteractableObjectEvent();
            onUpdateScreensOn = new InteractableObjectEvent();
            onUpdateOpacity = new InteractableObjectEvent();
            onCueAnimate = new InteractableObjectEvent();

        }

        else
            Destroy(this);
    }

}
