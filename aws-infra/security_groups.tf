# Create an EC2 security group for the web applications
resource "aws_security_group" "app_sg" {
  name   = "application"
  vpc_id = aws_vpc.vpc1.id

  tags = {
    Name = "application"
  }

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    security_groups = [aws_security_group.load_balancer.id]
  }
  ingress {
    from_port = 8765
    to_port   = 8765
    protocol  = "tcp"
    security_groups = [aws_security_group.load_balancer.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

#create a database security group
resource "aws_security_group" "rds_sg" {

  name   = "database"
  vpc_id = aws_vpc.vpc1.id

  tags = {
    Name = "database"
    Role = "public"
  }
}

resource "aws_security_group_rule" "database_rule" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds_sg.id
  source_security_group_id = aws_security_group.app_sg.id

}

resource "aws_security_group_rule" "database_rule2" {
  type                     = "egress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.rds_sg.id
  source_security_group_id = aws_security_group.app_sg.id
}

#create load balancer security group
resource "aws_security_group" "load_balancer" {
  name   = "load_balancer_sg"
  vpc_id = aws_vpc.vpc1.id
  tags = {
    Name = "load_balancer"
    Role = "public"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}