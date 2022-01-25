using UnityEngine;
using UnityEngine.UI;

namespace ReqRep
{
    public class UIManager : MonoBehaviour
    {
        [SerializeField] private Button sendRequestButton;

        private void Start()
        {
            EventManager.Instance.onClientBusy.AddListener(() => sendRequestButton.interactable = false);
            EventManager.Instance.onClientFree.AddListener(() => sendRequestButton.interactable = true);
            sendRequestButton.onClick.AddListener(() => EventManager.Instance.onSendRequest.Invoke());
        }
    }
}
