sudo docker stop lab_monitor
sudo docker rm lab_monitor
sudo docker run -it \
	--name lab_monitor \
	-p 80:80 \
	--privileged \
	-e LOG_LEVEL="debug" \
	-e MAX_WORKERS="1" \
	-v /home/bitmain/lab_monitor/app:/app \
	lab_monitor


