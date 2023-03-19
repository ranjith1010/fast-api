def label = "mypod-${UUID.randomUUID().toString()}"

podTemplate(label: label, containers: [
    containerTemplate(name: 'python', image: 'python:3.9-alpine', ttyEnabled: true, command: 'cat'),
]) {
    node(label) {
        stage('Get a Python project') {
            git 'https://github.com/ranjith1010/fast-api'
            container('python') {
                stage('Install Dependencies') {
                    sh "pip install -r requirements.txt"
                }
            }
        }
    }
}
