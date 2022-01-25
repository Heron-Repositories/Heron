using UnityEngine;
using UnityEngine.UI;

namespace PubSub
{
    public class UIManager : MonoBehaviour
    {
        [SerializeField] private Button startClient;
        [SerializeField] private Button stopClient;

        private void Start()
        {
            EventManager.Instance.onClientStarted.AddListener(() => stopClient.interactable = true);
            EventManager.Instance.onClientStopped.AddListener(() => startClient.interactable = true);
        
            stopClient.interactable = false;
            startClient.onClick.AddListener(() =>
            {
                startClient.interactable = false;
                EventManager.Instance.onStartClient.Invoke();
            });
        
            stopClient.onClick.AddListener(() =>
            {
                stopClient.interactable = false;
                EventManager.Instance.onStopClient.Invoke();
            });
        }
    }
}
