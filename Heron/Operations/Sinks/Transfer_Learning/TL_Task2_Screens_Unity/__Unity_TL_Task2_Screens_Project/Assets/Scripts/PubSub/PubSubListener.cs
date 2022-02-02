using System;
using System.Collections.Concurrent;
using System.Threading;
using NetMQ;
using NetMQ.Sockets;
using System.Text;

public class PubSubListener
{
    private Thread _clientThread;
    private readonly string _host;
    private readonly string _port;
    private readonly Action<string> _messageCallback;
    private bool _clientCancelled;

    private readonly ConcurrentQueue<string> _messageQueue = new ConcurrentQueue<string>();

    public PubSubListener(string host, string port, Action<string> messageCallback)
    {
        _host = host;
        _port = port;
        _messageCallback = messageCallback;
    }

    public void Start()
    {
        _clientCancelled = false;
        _clientThread = new Thread(ListenerWork);
        _clientThread.Start();
        EventManager.Instance.onClientStarted.Invoke();
    }

    public void Stop()
    {
        _clientCancelled = true;
        _clientThread?.Join();
        _clientThread = null;
        EventManager.Instance.onClientStopped.Invoke();
    }

    private void ListenerWork()
    {
        AsyncIO.ForceDotNet.Force();
        using (var subSocket = new SubscriberSocket())
        {
            subSocket.Options.ReceiveHighWatermark = 1000;
            subSocket.Connect($"tcp://{_host}:{_port}");
            subSocket.SubscribeToAnyTopic();
            while (!_clientCancelled)
            {
                if (!subSocket.TryReceiveFrameString(Encoding.ASCII, out var message)) continue;
                _messageQueue.Enqueue(message);
            }
            subSocket.Close();
        }
        NetMQConfig.Cleanup();
    }

    public void DigestMessage()
    {
        while (!_messageQueue.IsEmpty)
        {
            if (_messageQueue.TryDequeue(out var message))
                _messageCallback(message);
            else
                break;
        }
    }
}
