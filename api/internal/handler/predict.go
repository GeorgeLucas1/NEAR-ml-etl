package handler

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"pc-health-api/internal/db"
	"pc-health-api/internal/predictor"
)

type Prediction struct {
	Timestamp  string  `json:"timestamp"`
	Predicted  float64 `json:"predicted"`
	Lower      float64 `json:"lower,omitempty"`
	Upper      float64 `json:"upper,omitempty"`
	Actual     float64 `json:"actual,omitempty"`
	Confidence float64 `json:"confidence,omitempty"`
}

type ModelInfo struct {
	Algorithm   string  `json:"algorithm"`
	LastTrained string  `json:"last_trained"`
	R2Score     float64 `json:"r2_score"`
	NFeatures   int     `json:"n_features"`
}

func GetPrediction(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	features, err := db.GetLatestFeatures()
	if err != nil {
		json.NewEncoder(w).Encode(map[string]string{"error": "No prediction available"})
		return
	}

	pred, err := predictor.PredictCPU(features)
	if err != nil {
		json.NewEncoder(w).Encode(map[string]string{"error": "Prediction failed"})
		return
	}

	response := []Prediction{
		{
			Timestamp:  time.Now().Format(time.RFC3339),
			Predicted:  pred,
			Confidence: 0.85,
		},
	}

	json.NewEncoder(w).Encode(response)
}

func GetForecast(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	horizon := r.URL.Query().Get("horizon")
	if horizon == "" {
		horizon = "24"
	}
	h, _ := strconv.Atoi(horizon)

	features, err := db.GetLatestFeatures()
	if err != nil {
		json.NewEncoder(w).Encode([]Prediction{})
		return
	}

	forecasts, err := predictor.ForecastCPU(features, h)
	if err != nil {
		json.NewEncoder(w).Encode([]Prediction{})
		return
	}

	json.NewEncoder(w).Encode(forecasts)
}

func GetModelInfo(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	info := predictor.GetModelInfo()

	json.NewEncoder(w).Encode(info)
}

func GetBaseline(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	stats, err := db.GetBaselineStats()
	if err != nil {
		json.NewEncoder(w).Encode(map[string]map[string]float64{})
		return
	}

	json.NewEncoder(w).Encode(stats)
}
