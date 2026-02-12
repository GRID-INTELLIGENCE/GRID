terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "grid-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}

variable "environment" {
  description = "Deployment environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "GRID"
      ManagedBy   = "Terraform"
    }
  }
}

# VPC
resource "aws_vpc" "grid_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "grid-${var.environment}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "grid_igw" {
  vpc_id = aws_vpc.grid_vpc.id

  tags = {
    Name = "grid-${var.environment}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.grid_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "grid-${var.environment}-public-${count.index + 1}"
    Type = "Public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.grid_vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "grid-${var.environment}-private-${count.index + 1}"
    Type = "Private"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  count = var.environment == "prod" ? length(var.availability_zones) : 1
  vpc   = true

  tags = {
    Name = "grid-${var.environment}-nat-${count.index + 1}"
  }
}

resource "aws_nat_gateway" "grid_nat" {
  count         = var.environment == "prod" ? length(var.availability_zones) : 1
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "grid-${var.environment}-nat-${count.index + 1}"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.grid_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.grid_igw.id
  }

  tags = {
    Name = "grid-${var.environment}-public-rt"
  }
}

resource "aws_route_table" "private" {
  count  = var.environment == "prod" ? length(var.availability_zones) : 1
  vpc_id = aws_vpc.grid_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.grid_nat[count.index].id
  }

  tags = {
    Name = "grid-${var.environment}-private-rt-${count.index + 1}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = var.environment == "prod" ? length(var.availability_zones) : length(var.availability_zones)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.environment == "prod" ? aws_route_table.private[count.index].id : aws_route_table.private[0].id
}

# Security Groups
resource "aws_security_group" "grid_api" {
  name_prefix = "grid-api-${var.environment}-"
  vpc_id      = aws_vpc.grid_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "grid-api-${var.environment}"
  }
}

resource "aws_security_group" "grid_database" {
  name_prefix = "grid-db-${var.environment}-"
  vpc_id      = aws_vpc.grid_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.grid_api.id]
    description     = "PostgreSQL"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "grid-database-${var.environment}"
  }
}

# RDS PostgreSQL Database
resource "aws_db_subnet_group" "grid_db" {
  name       = "grid-${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "grid-${var.environment}-db-subnet-group"
  }
}

resource "aws_db_instance" "grid_database" {
  identifier = "grid-${var.environment}-database"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.environment == "prod" ? "db.r6g.large" : "db.t4g.medium"

  allocated_storage     = var.environment == "prod" ? 100 : 20
  max_allocated_storage = var.environment == "prod" ? 1000 : 100

  db_name  = "grid"
  username = "grid"
  password = var.database_password

  db_subnet_group_name   = aws_db_subnet_group.grid_db.name
  vpc_security_group_ids = [aws_security_group.grid_database.id]

  multi_az               = var.environment == "prod"
  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = var.environment != "prod"

  tags = {
    Name = "grid-${var.environment}-database"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "grid_cache" {
  name       = "grid-${var.environment}-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "grid_cache" {
  cluster_id           = "grid-${var.environment}-cache"
  engine              = "redis"
  node_type           = var.environment == "prod" ? "cache.r6g.large" : "cache.t4g.micro"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379

  subnet_group_name  = aws_elasticache_subnet_group.grid_cache.name
  security_group_ids = [aws_security_group.grid_database.id]

  tags = {
    Name = "grid-${var.environment}-cache"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "grid_cluster" {
  name = "grid-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = var.environment == "prod" ? "enabled" : "disabled"
  }

  tags = {
    Name = "grid-${var.environment}-cluster"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "grid_logs" {
  name              = "/ecs/grid-${var.environment}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name = "grid-${var.environment}-logs"
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.grid_vpc.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.grid_database.endpoint
}

output "cache_endpoint" {
  description = "Redis cache endpoint"
  value       = aws_elasticache_cluster.grid_cache.cache_nodes[0].address
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.grid_cluster.name
}
