kubectl create ns monitoring 


helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update



helm install prometheus prometheus-community/prometheus  -n monitoring 

Expose the service:

kubectl edit service >>>>> nodeport 



helm repo add grafana https://grafana.github.io/helm-charts 
helm repo update


helm install grafana grafana/grafana -n monitoring 


Kubectl edit service  >>>> nodeport



NAME                                                READY   STATUS    RESTARTS        AGE
grafana-5bc94448cb-rc7wt                            1/1     Running   1               5d23h
prometheus-alertmanager-0                           1/1     Running   0               3d21h
prometheus-kube-state-metrics-76f8bff48-fqb64       1/1     Running   1               9d
prometheus-prometheus-node-exporter-6z477           1/1     Running   1               9d
prometheus-prometheus-node-exporter-htskm           1/1     Running   1 (3d21h ago)   9d
prometheus-prometheus-pushgateway-cd9c95968-jckgh   1/1     Running   1               9d
prometheus-server-974f8785f-5jw5b                   2/2     Running   0               3d21h




kubectl get secret grafana -n monitoring -o jsonpath="{.data}" | jq .

# Fetch username
kubectl get secret grafana -n monitoring -o jsonpath="{.data.admin-user}" | base64 --decode; echo

# Fetch password
kubectl get secret grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 --decode; echo
