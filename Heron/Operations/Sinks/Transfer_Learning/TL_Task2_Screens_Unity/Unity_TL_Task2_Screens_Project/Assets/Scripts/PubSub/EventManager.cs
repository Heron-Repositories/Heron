using UnityEngine;
using UnityEngine.Events;

namespace PubSub
{
    public class EventManager : MonoBehaviour
    {
        public static EventManager Instance;

        private void Awake()
        {
            if (Instance == null)
            {
                Instance = this;
            
                onStartClient = new UnityEvent();
                onClientStarted = new UnityEvent();
                onStopClient = new UnityEvent();
                onClientStopped = new UnityEvent();
            }
            else
                Destroy(this);
        }

        public UnityEvent onStartClient;
        public UnityEvent onClientStarted;
        public UnityEvent onStopClient;
        public UnityEvent onClientStopped;
    }
}