using UnityEngine;

namespace ReqRep
{
    public class ReqRepClient : MonoBehaviour
    {
        [SerializeField] private string host;
        [SerializeField] private string port;
        private ReqRepListener _listener;

        private void Start()
        {
            _listener = new ReqRepListener(host, port, HandleMessage);
            _listener.RequestMessage();
        }

        private void HandleMessage(string message)
        {
            Debug.Log(message);
        }
    }
}