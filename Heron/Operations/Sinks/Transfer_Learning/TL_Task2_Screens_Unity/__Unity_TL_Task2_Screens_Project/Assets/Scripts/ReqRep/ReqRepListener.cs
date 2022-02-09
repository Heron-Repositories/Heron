using System;
using NetMQ;
using NetMQ.Sockets;


public class ReqRepListener
{
    private readonly string _host;
    private readonly string _port;
    private readonly Action<string> _messageCallback;

    public ReqRepListener(string host, string port, Action<string> messageCallback)
    {
        _host = host;
        _port = port;
        _messageCallback = messageCallback;
    }

    public void RequestMessage()
    {
        var messageReceived = false;
        string message = "";
        AsyncIO.ForceDotNet.Force();

        var timeout = new TimeSpan(0, 0, 2);
        using (var socket = new RequestSocket())
        {
            socket.Connect($"tcp://{_host}:{_port}");
            if (socket.TrySendFrame("Unity has started"))
            {
                messageReceived = socket.TryReceiveFrameString(timeout, out message);
            }
        }

        if (!messageReceived)
            message = "No message from Heron";
        _messageCallback(message);
    }
}
