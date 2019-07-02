sudo jack_connect system:capture_1 SuperCollider:in_1
sudo jack_connect system:capture_2 SuperCollider:in_2
sudo jack_connect SuperCollider:out_1 system:playback_1
sudo jack_connect SuperCollider:out_2 system:playback_2
