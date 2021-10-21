// Does not need to be changed
VARMAP = [:]
def rootDir = pwd()
new File("${rootDir}/app.param").readLines().each { line ->
    def eq = line.indexOf('=')
    def key = line[0..(eq-1)]
    def value = line[eq+1..(line.length()-1)]
    VARMAP["${key}"] = "${value}"
}
VARMAP.each{entry -> println "$entry.key: $entry.value"}
DOCKER_CREDENTIAL = "gve-devnet-gen-containers"
OC_CREDENTIAL = "gvedevnet-oc"
GITHUB_CREDENTIAL = "8b4a7b24-682e-4109-8d71-ccf9226106b1"
CONTACT = "${VARMAP['CEC_ID']}@cisco.com"
APP_IMAGE = "containers.cisco.com/gvedevnet/${VARMAP['APP_NAME']}"
APP_URL = "gve-devnet-${VARMAP['APP_NAME']}.cisco.com"
JENKINS_TOKEN = "1108ffa8bea81062132e290c3c94a6acdd"
GIT_TOKEN = "f056889ec438e663eca9c23b3791e342d03f5d72"