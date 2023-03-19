pipeline{
    environment {
        build_version = "1+${BUILD_NUMBER}"
    }
    agent {
        docker { image 'python:3' }
    }

    stages {
        stage('Test pip'){
            steps{
                sh 'pip --version'
            }
        }
        stage('Clone github repo'){
            steps {
                git url: 'https://github.com/ranjith1010/fast-api', branch: 'main'
            }
        }

        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt --user'
            }
        }

        stage ('Commit in prod branch') {
            steps {
                sh '''
                    echo "commit prod branch"
                '''
            }

        }

        
        
    }
}
