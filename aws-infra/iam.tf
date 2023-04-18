resource "aws_iam_role" "s3_role" {
  name = "s3_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_policy_attachment" {
  role       = aws_iam_role.s3_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role" "EC2-CSYE6225" {
  name = "EC2-CSYE6225"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "CloudWatch_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.EC2-CSYE6225.name
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "EC2InstanceProfile-CSYE6225"

  role = aws_iam_role.EC2-CSYE6225.name
  role = aws_iam_role.s3_role.name
}
