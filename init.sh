sudo docker stop lab_monitor
sudo docker rm lab_monitor
sudo docker run -it \
	--name lab_monitor \
	-p 6080:6080 \
	-v /home/bitmain/lab_monitor:/mnt/lab_monitor \
	continuumio/anaconda3
