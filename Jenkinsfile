pipeline {
  agent {
    label 'arm'
  }
  environment {
    gateway='https://gateway.christoffernissen.me'
  }
  stages {
    stage('clone down') {
      steps {
        stash name: 'code', excludes: '.git'
      }
      post {
        always {
          deleteDir()
        }
      }
    }
    stage('Build') {
      options {
        skipDefaultCheckout()
      }
      steps {
        unstash 'code'
        sh 'faas-cli build -f truckfactor.yml'
      }
    }
    stage('Push') {
      options {
        skipDefaultCheckout()
      }
      environment {
        InfluxDBToken = credentials('InfluxDBToken')
        DOCKERCREDS = credentials('docker_login') 
        OPENFAASCREDS = credentials('gateway_credentials') 
      }
      when { branch "master" } 
      steps {
        unstash 'code' 
        sh 'echo "$DOCKERCREDS_PSW" | docker login -u "$DOCKERCREDS_USR" --password-stdin' 
        sh 'echo "$OPENFAASCREDS_PSW" | faas-cli login -g $gateway --password-stdin'
        sh 'faas-cli -g $gateway up -f truckfactor.yml' 
      } 
   }
  }  
}
