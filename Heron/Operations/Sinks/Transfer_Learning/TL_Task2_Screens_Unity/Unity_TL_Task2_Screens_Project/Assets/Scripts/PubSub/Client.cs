using UnityEngine;

namespace PubSub
{
    public class Client : MonoBehaviour
    {
        public enum ClientStatus
        {
            Inactive,
            Activating,
            Active,
            Deactivating
        }
    
        [SerializeField] private string host;
        [SerializeField] private string port;
        private Listener _listener;
        private ClientStatus _clientStatus = ClientStatus.Inactive;

        private void Start()
        {
            _listener = new Listener(host, port, HandleMessage);
            EventManager.Instance.onStartClient.AddListener(OnStartClient);
            EventManager.Instance.onClientStarted.AddListener(() => _clientStatus = ClientStatus.Active);
            EventManager.Instance.onStopClient.AddListener(OnStopClient);
            EventManager.Instance.onClientStopped.AddListener(() => _clientStatus = ClientStatus.Inactive);
        }

        private void Update()
        {
            if (_clientStatus == ClientStatus.Active)
                _listener.DigestMessage();
        }

        private void OnDestroy()
        {
            if (_clientStatus != ClientStatus.Inactive)
                OnStopClient();
        }

        private void HandleMessage(string message)
        {
            Debug.Log(message);
        }

        private void OnStartClient()
        {
            Debug.Log("Starting client...");
            _clientStatus = ClientStatus.Activating;
            _listener.Start();
            Debug.Log("Client started!");
        }

        private void OnStopClient()
        {
            Debug.Log("Stopping client...");
            _clientStatus = ClientStatus.Deactivating;
            _listener.Stop();
            Debug.Log("Client stopped!");
        }
    }
}