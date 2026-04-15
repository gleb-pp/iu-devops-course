{{- define "mychart.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "mychart.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}