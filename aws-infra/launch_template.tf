data "template_file" "user_data" {

  template = <<EOF
#!/bin/bash
    cd /bin
    sudo yum update -y
    echo "username=${aws_db_instance.csye6225db.username}" >> /home/ec2-user/webapp/.env
    echo "password=${var.dbpassword}" >> /home/ec2-user/webapp/.env
    echo "host=${aws_db_instance.csye6225db.address}" >> /home/ec2-user/webapp/.env
    echo "s3=${aws_s3_bucket.private_bucket.bucket}" >> /home/ec2-user/webapp/.env
   echo "secretkey=${var.secret_key}" >> /home/ec2-user/webapp/.env
echo "accesskey=${var.access_key}" >> /home/ec2-user/webapp/.env
    sudo systemctl daemon-reload
    sudo systemctl daemon-reload
    sudo systemctl enable app.service
    sudo systemctl restart app.service
    sudo systemctl start app.service
 EOF
 
}

resource "aws_launch_template" "lt" {
  name          = "asg_launch_config"
  image_id      = var.ami
  instance_type = var.instance_type
  key_name      = var.key_name
  user_data = base64encode(data.template_file.user_data.rendered)
  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_instance_profile.name
  }

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.app_sg.id]
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 30
      delete_on_termination = true
      volume_type           = "gp2"
      encrypted             = true
      kms_key_id            = aws_kms_key.ebs_encrypt.arn
    }
  }

  tags = {
    Name = "asg_launch_config"
  }
}