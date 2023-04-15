resource "aws_autoscaling_group" "asg" {

  name             = "csye6225-asg-spring2023"
  default_cooldown = 60
  max_size         = 3
  min_size         = 1
  desired_capacity = 1
  vpc_zone_identifier = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id, aws_subnet.public_subnet_3.id]

  tag {
    key = "name"
    value = "webapp-instance-csye6225-ec2"
    propagate_at_launch = true
  }

  launch_template {
    id = aws_launch_template.lt.id
    version = "$Latest"
  }

  target_group_arns = [
    aws_lb_target_group.alb_tg.arn
  ]
}

resource "aws_autoscaling_policy" "scale_up_policy" {
  name               = "scale_up_policy"
  scaling_adjustment = 1
  cooldown               = 60
  autoscaling_group_name = aws_autoscaling_group.asg.name
  adjustment_type        = "ChangeInCapacity"
}

resource "aws_autoscaling_policy" "scale_down_policy" {
  name = "scale_down_policy"
  cooldown               = 60
  autoscaling_group_name = aws_autoscaling_group.asg.name
  adjustment_type    = "ChangeInCapacity"
  scaling_adjustment = -1
}