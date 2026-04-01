package handler

import (
	"encoding/json"
	"net/http"
	"strconv"

	"pc-health-api/internal/db"
)

type AnomalyResponse struct {
	Timestamp string  `json:"timestamp"`
	Metric    string  `json:"metric"`
	Value     float64 `json:"value"`
	Threshold float64 `json:"threshold"`
	Severity  string  `json:"severity"`
	Type      string  `json:"type"`
}

func GetAnomalies(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	anomalies, err := db.GetRecentAnomalies(20)
	if err != nil {
		json.NewEncoder(w).Encode([]AnomalyResponse{})
		return
	}

	var response []AnomalyResponse
	for _, a := range anomalies {
		response = append(response, AnomalyResponse{
			Timestamp: a.Timestamp.Format("2006-01-02T15:04:05Z"),
			Metric:    a.Metric,
			Value:     a.Value,
			Threshold: a.Threshold,
			Severity:  a.Severity,
			Type:      a.Type,
		})
	}

	if response == nil {
		response = []AnomalyResponse{}
	}

	json.NewEncoder(w).Encode(response)
}

func GetAnomaliesHistory(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	days := r.URL.Query().Get("days")
	if days == "" {
		days = "7"
	}
	d, _ := strconv.Atoi(days)

	anomalies, err := db.GetAnomaliesHistory(d)
	if err != nil {
		json.NewEncoder(w).Encode([]AnomalyResponse{})
		return
	}

	var response []AnomalyResponse
	for _, a := range anomalies {
		response = append(response, AnomalyResponse{
			Timestamp: a.Timestamp.Format("2006-01-02T15:04:05Z"),
			Metric:    a.Metric,
			Value:     a.Value,
			Threshold: a.Threshold,
			Severity:  a.Severity,
			Type:      a.Type,
		})
	}

	if response == nil {
		response = []AnomalyResponse{}
	}

	json.NewEncoder(w).Encode(response)
}
