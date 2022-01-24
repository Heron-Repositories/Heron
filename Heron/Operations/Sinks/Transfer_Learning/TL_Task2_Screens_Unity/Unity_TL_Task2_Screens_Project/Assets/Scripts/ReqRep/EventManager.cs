using UnityEngine;
using UnityEngine.Events;

namespace ReqRep
{
    public class EventManager : MonoBehaviour
    {
        public static EventManager Instance;

        private void Awake()
        {
            if (Instance == null)
            {
                Instance = this;
            
                onSendRequest = new UnityEvent();
                onClientBusy = new UnityEvent();
                onClientFree = new UnityEvent();
            }
            else
                Destroy(this);
        }

        public UnityEvent onSendRequest;
        public UnityEvent onClientBusy;
        public UnityEvent onClientFree;
    }
}