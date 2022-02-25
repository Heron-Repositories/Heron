using UnityEngine;
using UnityEngine.Events;
using System.Linq;

public class PubSubClient : MonoBehaviour
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
    private PubSubListener _listener;
    private ClientStatus _clientStatus = ClientStatus.Inactive;

    private void Start()
    {
        _listener = new PubSubListener(host, port, HandleMessage);
        EventManager.Instance.onStartClient.AddListener(OnStartClient);
        EventManager.Instance.onClientStarted.AddListener(() => _clientStatus = ClientStatus.Active);
        EventManager.Instance.onStopClient.AddListener(OnStopClient);
        EventManager.Instance.onClientStopped.AddListener(() => _clientStatus = ClientStatus.Inactive);

        OnStartClient();
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
        //Debug.Log(message);
        string message_data = message.Substring(message.IndexOf(":")).Substring(1);
        //Debug.Log(message_data);

        if (message.Contains("Screens:"))
        {
            EventManager.Instance.onUpdateScreensOn.Invoke(message_data);
        }

        if (message.Contains("MovementType:"))
        {
            EventManager.Instance.onUpdateMovementType.Invoke(message_data);
        }

        if (message.Contains("Opacity:"))
        {
            EventManager.Instance.onUpdateOpacity.Invoke(message_data);
        }

        if (message.Contains("Coordinates:"))
        {
            EventManager.Instance.onUpdatedMotion.Invoke(message_data);
        }

        
    }

    private void OnStartClient()
    {
        //Debug.Log("Starting PubSub client...");
        _clientStatus = ClientStatus.Activating;
        _listener.Start();
        //Debug.Log("PubSub Client started!");
    }

    private void OnStopClient()
    {
        //Debug.Log("Stopping PubSub client...");
        _clientStatus = ClientStatus.Deactivating;
        _listener.Stop();
        //Debug.Log("PubSub Client stopped!");
    }
}
