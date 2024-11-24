# AWS EC2 Management Project

This project is part of the **Cloud Computing Term Project** for the **2024 2nd Semester**. The goal is to implement AWS EC2 instance management functionalities using **AWS Java SDK** and **REST API**. The project covers key concepts and tasks from Chapter 9.

---

## 📜 Features

The project supports the following commands:

1. **listinstance**: Lists all running EC2 instances.
2. **availablezones**: Retrieves the available availability zones in the selected region.
3. **startinstance**: Starts a stopped EC2 instance.
4. **availableregions**: Lists all available AWS regions.
5. **stopinstance**: Stops a running EC2 instance.
6. **createinstance**: Launches a new EC2 instance.
7. **rebootinstance**: Reboots an existing EC2 instance.
8. **listimages**: Retrieves a list of available AMIs (Amazon Machine Images).
9. **quit**: Exits the application.

---

## 🛠️ Technologies Used

- **Java**: Primary programming language.
- **AWS Java SDK**: Interacts with AWS services.
- **Spring Boot**: Framework for building REST APIs.
- **AWS EC2**: Cloud service for managing virtual machines.
- **CondorPool**: Integrated for instance orchestration.

---

## 🚀 Getting Started

### Prerequisites

1. **AWS Account**:
   - Create an IAM user with programmatic access.
   - Attach the necessary permissions for EC2 management.
   - Obtain the `awsAccessKeyId` and `awsSecretAccessKey`.

2. **Development Environment**:
   - Java JDK 17 or higher.
   - Maven or Gradle for dependency management.
   - AWS CLI (optional, for additional manual testing).

---

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/aws-ec2-management.git
   cd aws-ec2-management
