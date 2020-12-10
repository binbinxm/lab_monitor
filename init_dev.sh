sudo docker stop lab_monitor
sudo docker rm lab_monitor
sudo docker run -it \
	--name lab_monitor \
	-p 6080:80 \
	--privileged \
	--restart always \
	-e LOG_LEVEL="debug" \
	-v /home/bitmain/lab_monitor/app:/app \
	lab_monitor /start-reload.sh
