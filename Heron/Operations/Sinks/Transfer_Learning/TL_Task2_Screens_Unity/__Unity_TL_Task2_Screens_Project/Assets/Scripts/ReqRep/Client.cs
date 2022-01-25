using UnityEngine;

namespace ReqRep
{
    public class Client : MonoBehaviour
    {
        [SerializeField] private string host;
        [SerializeField] private string port;
        private Listener _listener;

        private void Start()
        {
            _listener = new Listener(host, port, HandleMessage);
            EventManager.Instance.onSendRequest.AddListener(OnClientRequest);
        }

        private void OnClientRequest()
        {
            EventManager.Instance.onClientBusy.Invoke();
            _listener.RequestMessage();
            EventManager.Instance.onClientFree.Invoke();
        }

        private void HandleMessage(string message)
        {
            Debug.Log(message);
        }
    }
}