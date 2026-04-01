package handler

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"pc-health-api/internal/db"
)

type MetricsResponse struct {
	Timestamp string  `json:"timestamp"`
	CPUUsage  float64 `json:"cpu_usage"`
	CPUModel  string  `json:"cpu_model"`
	CPUtemp   float64 `json:"cpu_temp"`
	RAMUsage  float64 `json:"ram_usage"`
	RAMTotal  float64 `json:"ram_total"`
	RAMUsed   float64 `json:"ram_used"`
	DiskUsage float64 `json:"disk_usage"`
	DiskTotal float64 `json:"disk_total"`
	DiskUsed  float64 `json:"disk_used"`
	GPUUsage  float64 `json:"gpu_usage"`
	GPUModel  string  `json:"gpu_model"`
	DiskRead  float64 `json:"disk_read"`
	DiskWrite float64 `json:"disk_write"`
	Network   Network `json:"network"`
}

type Network struct {
	BytesSent float64 `json:"bytes_sent"`
	BytesRecv float64 `json:"bytes_recv"`
}

type HistoryResponse struct {
	Timestamp string  `json:"timestamp"`
	Value     float64 `json:"value"`
}

func GetLatestMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	m, err := db.GetLatestMetrics()
	if err != nil {
		json.NewEncoder(w).Encode(map[string]string{"error": "No metrics available"})
		return
	}

	// Formatar timestamp para o frontend
	timestamp := m.Timestamp
	if timestamp == "" {
		timestamp = time.Now().Format(time.RFC3339)
	}

	response := MetricsResponse{
		Timestamp: timestamp,
		CPUUsage:  m.CPUUsage,
		CPUModel:  "CPU",
		CPUtemp:   m.CPUtemp,
		RAMUsage:  m.RAMUsage,
		RAMTotal:  m.RAMTotal,
		RAMUsed:   m.RAMUsed,
		DiskUsage: 50.0,
		DiskTotal: 500.0,
		DiskUsed:  250.0,
		GPUUsage:  m.GPUUsage,
		GPUModel:  "GPU",
		DiskRead:  m.DiskRead,
		DiskWrite: m.DiskWrite,
		Network: Network{
			BytesSent: m.NetSent,
			BytesRecv: m.NetRecv,
		},
	}

	json.NewEncoder(w).Encode(response)
}

func GetMetricsHistory(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	hours := r.URL.Query().Get("hours")
	if hours == "" {
		hours = "6"
	}
	h, _ := strconv.Atoi(hours)

	metrics, err := db.GetMetricsHistory(h)
	if err != nil {
		json.NewEncoder(w).Encode([]MetricsResponse{})
		return
	}

	var metricParam = "cpu_usage"
	param := r.URL.Query().Get("metric")
	if param != "" {
		metricParam = param
	}

	var history []HistoryResponse
	for _, m := range metrics {
		var value float64
		switch metricParam {
		case "ram_usage":
			value = m.RAMUsage
		case "gpu_usage":
			value = m.GPUUsage
		case "disk_usage":
			value = m.DiskUsage
		case "network_bytes":
			value = m.NetSent + m.NetRecv
		default:
			value = m.CPUUsage
		}
		history = append(history, HistoryResponse{
			Timestamp: m.Timestamp,
			Value:     value,
		})
	}

	if history == nil {
		history = []HistoryResponse{}
	}

	json.NewEncoder(w).Encode(history)
}

func HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"service": "pc-health-api",
	})
}

func IngestMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		json.NewEncoder(w).Encode(map[string]string{"error": "Method not allowed"})
		return
	}

	var payload db.IngestPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "Invalid payload"})
		return
	}

	if err := db.InsertMetrics(&payload); err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": "Failed to insert metrics"})
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
