pipeline {
    agent none
    environment {
        DOCKER_REGISTRY = "containers.cisco.com"
        PROJECT_NAME = "gvedevnetdemos"
        APP_PORT = "5000"
        REPLICA_COUNT = 1
        WEBEX_BOT_TOKEN = "NTQ5OTdlYWEtYzYwMy00YWJmLWI5ZDItMzk2NWY1OWYzOGFjOWQ1MTA3ODQtYzAz_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
    }
    stages {
        stage('Build') {
            agent any

            steps {
                echo 'Building..'
                echo 'test'
                sh 'sudo systemctl start docker.service &> /dev/null &'
                sh 'sleep 10'

                script { 
                    // Load environment
                    def rootDir = pwd()
                    sh "source ./app.param"
                    load "${rootDir}/app.groovy"
                    
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIAL}") {
                        def customImage = docker.build("${DOCKER_REGISTRY}/gvedevnet/${VARMAP['APP_NAME']}")
                        customImage.push()
                    }
                }
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
            }
        }
        stage('Deploy') {
            agent any

            steps {
                echo 'Starting deploy....'
                script {
                    withEnv(["PATH+OC=${tool 'oc1.3.2'}"]) {
                        openshift.withCluster("gvedevnet", "${OC_CREDENTIAL}") {
                            openshift.withProject("${PROJECT_NAME}") {
                                // Load variables
                                def rootDir = pwd()
                                sh "source ./app.param"
                                load "${rootDir}/app.groovy"

                                echo "Logging in..."
                                openshift.raw("login")

                                echo "Cleaning up..."
                                def pods = openshift.selector("all", [ app : "${VARMAP['APP_NAME']}" ])
                                echo "Removing objects: ${pods.names()}"
                                pods.delete()
                                sh 'sleep 10'

                                echo "Creating objects..."
                                def models = openshift.process("-f", "gve-app-template.yaml", "-p", "APP_NAME=${VARMAP['APP_NAME']}","-p", "APP_PORT=${APP_PORT}","-p", "APP_IMAGE=${VARMAP['APP_IMAGE']}","-p", "REPLICA_COUNT=${REPLICA_COUNT}")

                                echo "Deloying objects..."
                                def result = openshift.create(models)
                            }
                        }
                    }
                }
            }
        }

        stage("Report") {
            agent any

            steps {
                script {
                    // Load environment
                    def rootDir = pwd()
                    sh "source ./app.param"
                    load "${rootDir}/app.groovy"

                    echo "Reporting..."

                    withEnv(["APP_NAME=${VARMAP['APP_NAME']}", "APP_URL=${APP_URL}", "CONTACT=${CONTACT}"]) {
                        sh '/usr/bin/python3 -m pip install -r requirements.txt'
                        sh '''
                            echo -e "import app \nimport os \napp.notify_deployment('${APP_NAME}', '${APP_URL}', '${CONTACT}', '${WEBEX_BOT_TOKEN}')" | /usr/bin/python3
                        '''
                    }
                }
            }
        }
    }
}