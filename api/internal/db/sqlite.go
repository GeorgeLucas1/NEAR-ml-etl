package db

import (
	"database/sql"
	"log"
	"sync"
	"time"

	_ "modernc.org/sqlite"
)

var (
	db   *sql.DB
	once sync.Once
)

type Metrics struct {
	ID        int64
	Timestamp string
	CPUUsage  float64
	CPUtemp   float64
	RAMUsage  float64
	RAMTotal  float64
	RAMUsed   float64
	DiskUsage float64
	DiskRead  float64
	DiskWrite float64
	NetSent   float64
	NetRecv   float64
	GPUUsage  float64
	GPUtemp   float64
	Processed int64
}

type CleanMetrics struct {
	ID        int64
	Timestamp time.Time
	CPUUsage  float64
	CPUtemp   float64
	RAMUsage  float64
	DiskUsage float64
	DiskRead  float64
	DiskWrite float64
	NetSent   float64
	NetRecv   float64
	GPUUsage  float64
	GPUtemp   float64
	Processed bool
}

type Features struct {
	ID             int64
	Timestamp      string
	CPUUsageMean   float64
	CPUUsageStd    float64
	CPUUsageMax    float64
	CPUUsageMin    float64
	CPUUsageDelta  float64
	CPUUsageTrend  float64
	CPUtempMean    float64
	CPUtempStd     float64
	CPUtempMax     float64
	CPUtempMin     float64
	CPUtempDelta   float64
	CPUtempTrend   float64
	RAMUsageMean   float64
	RAMUsageStd    float64
	RAMUsageMax    float64
	RAMUsageMin    float64
	RAMUsageDelta  float64
	RAMUsageTrend  float64
	DiskUsageMean  float64
	DiskUsageStd   float64
	DiskUsageMax   float64
	DiskUsageMin   float64
	DiskUsageDelta float64
	DiskUsageTrend float64
	DiskReadMean   float64
	DiskReadStd    float64
	DiskReadMax    float64
	DiskReadMin    float64
	DiskReadDelta  float64
	DiskReadTrend  float64
	DiskWriteMean  float64
	DiskWriteStd   float64
	DiskWriteMax   float64
	DiskWriteMin   float64
	DiskWriteDelta float64
	DiskWriteTrend float64
	NetSentMean    float64
	NetSentStd     float64
	NetSentMax     float64
	NetSentMin     float64
	NetSentDelta   float64
	NetSentTrend   float64
	NetRecvMean    float64
	NetRecvStd     float64
	NetRecvMax     float64
	NetRecvMin     float64
	NetRecvDelta   float64
	NetRecvTrend   float64
	GPUUsageMean   float64
	GPUUsageStd    float64
	GPUUsageMax    float64
	GPUUsageMin    float64
	GPUUsageDelta  float64
	GPUUsageTrend  float64
	GPUtempMean    float64
	GPUtempStd     float64
	GPUtempMax     float64
	GPUtempMin     float64
	GPUtempDelta   float64
	GPUtempTrend   float64
}

type Anomaly struct {
	ID        int64
	Timestamp time.Time
	Metric    string
	Value     float64
	Threshold float64
	Severity  string
	Type      string
}

func Init(dbPath string) error {
	var err error
	once.Do(func() {
		db, err = sql.Open("sqlite", dbPath)
		if err != nil {
			return
		}
		db.SetMaxOpenConns(1)
		err = db.Ping()
		if err != nil {
			return
		}
		log.Println("Database connected:", dbPath)
	})
	return err
}

func GetDB() *sql.DB {
	return db
}

func Close() error {
	if db != nil {
		return db.Close()
	}
	return nil
}

func GetLatestMetrics() (*Metrics, error) {
	var m Metrics
	query := `SELECT id, timestamp, cpu_usage, cpu_temp, ram_usage, ram_total, ram_used,
		disk_usage, disk_read, disk_write, net_sent, net_recv, gpu_usage, gpu_temp, processed
		FROM raw_metrics ORDER BY timestamp DESC LIMIT 1`

	row := db.QueryRow(query)
	err := row.Scan(&m.ID, &m.Timestamp, &m.CPUUsage, &m.CPUtemp, &m.RAMUsage, &m.RAMTotal, &m.RAMUsed,
		&m.DiskUsage, &m.DiskRead, &m.DiskWrite, &m.NetSent, &m.NetRecv, &m.GPUUsage, &m.GPUtemp, &m.Processed)
	if err != nil {
		return nil, err
	}
	return &m, nil
}

func GetMetricsHistory(hours int) ([]Metrics, error) {
	query := `SELECT id, timestamp, cpu_usage, cpu_temp, ram_usage, ram_total, ram_used,
		disk_usage, disk_read, disk_write, net_sent, net_recv, gpu_usage, gpu_temp, processed
		FROM raw_metrics 
		WHERE timestamp > datetime('now', '-' || ? || ' hours')
		ORDER BY timestamp ASC`

	rows, err := db.Query(query, hours)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var metrics []Metrics
	for rows.Next() {
		var m Metrics
		err := rows.Scan(&m.ID, &m.Timestamp, &m.CPUUsage, &m.CPUtemp, &m.RAMUsage, &m.RAMTotal, &m.RAMUsed,
			&m.DiskUsage, &m.DiskRead, &m.DiskWrite, &m.NetSent, &m.NetRecv, &m.GPUUsage, &m.GPUtemp, &m.Processed)
		if err != nil {
			continue
		}
		metrics = append(metrics, m)
	}
	return metrics, nil
}

func GetLatestFeatures() (*Features, error) {
	query := `SELECT id, timestamp,
		cpu_usage_mean, cpu_usage_std, cpu_usage_max, cpu_usage_min, cpu_usage_delta, cpu_usage_trend,
		cpu_temp_mean, cpu_temp_std, cpu_temp_max, cpu_temp_min, cpu_temp_delta, cpu_temp_trend,
		ram_usage_mean, ram_usage_std, ram_usage_max, ram_usage_min, ram_usage_delta, ram_usage_trend,
		disk_usage_mean, disk_usage_std, disk_usage_max, disk_usage_min, disk_usage_delta, disk_usage_trend,
		disk_read_mean, disk_read_std, disk_read_max, disk_read_min, disk_read_delta, disk_read_trend,
		disk_write_mean, disk_write_std, disk_write_max, disk_write_min, disk_write_delta, disk_write_trend,
		net_sent_mean, net_sent_std, net_sent_max, net_sent_min, net_sent_delta, net_sent_trend,
		net_recv_mean, net_recv_std, net_recv_max, net_recv_min, net_recv_delta, net_recv_trend,
		gpu_usage_mean, gpu_usage_std, gpu_usage_max, gpu_usage_min, gpu_usage_delta, gpu_usage_trend,
		gpu_temp_mean, gpu_temp_std, gpu_temp_max, gpu_temp_min, gpu_temp_delta, gpu_temp_trend
		FROM features ORDER BY timestamp DESC LIMIT 1`

	row := db.QueryRow(query)

	var f Features
	var createdAt string // ignorar created_at
	err := row.Scan(&f.ID, &f.Timestamp,
		&f.CPUUsageMean, &f.CPUUsageStd, &f.CPUUsageMax, &f.CPUUsageMin, &f.CPUUsageDelta, &f.CPUUsageTrend,
		&f.CPUtempMean, &f.CPUtempStd, &f.CPUtempMax, &f.CPUtempMin, &f.CPUtempDelta, &f.CPUtempTrend,
		&f.RAMUsageMean, &f.RAMUsageStd, &f.RAMUsageMax, &f.RAMUsageMin, &f.RAMUsageDelta, &f.RAMUsageTrend,
		&f.DiskUsageMean, &f.DiskUsageStd, &f.DiskUsageMax, &f.DiskUsageMin, &f.DiskUsageDelta, &f.DiskUsageTrend,
		&f.DiskReadMean, &f.DiskReadStd, &f.DiskReadMax, &f.DiskReadMin, &f.DiskReadDelta, &f.DiskReadTrend,
		&f.DiskWriteMean, &f.DiskWriteStd, &f.DiskWriteMax, &f.DiskWriteMin, &f.DiskWriteDelta, &f.DiskWriteTrend,
		&f.NetSentMean, &f.NetSentStd, &f.NetSentMax, &f.NetSentMin, &f.NetSentDelta, &f.NetSentTrend,
		&f.NetRecvMean, &f.NetRecvStd, &f.NetRecvMax, &f.NetRecvMin, &f.NetRecvDelta, &f.NetRecvTrend,
		&f.GPUUsageMean, &f.GPUUsageStd, &f.GPUUsageMax, &f.GPUUsageMin, &f.GPUUsageDelta, &f.GPUUsageTrend,
		&f.GPUtempMean, &f.GPUtempStd, &f.GPUtempMax, &f.GPUtempMin, &f.GPUtempDelta, &f.GPUtempTrend,
	)
	_ = createdAt // ignore
	if err != nil {
		return nil, err
	}
	return &f, nil
}

func GetRecentAnomalies(limit int) ([]Anomaly, error) {
	query := `SELECT id, timestamp, metric, value, threshold, severity, type
		FROM anomalies ORDER BY timestamp DESC LIMIT ?`

	rows, err := db.Query(query, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var anomalies []Anomaly
	for rows.Next() {
		var a Anomaly
		err := rows.Scan(&a.ID, &a.Timestamp, &a.Metric, &a.Value, &a.Threshold, &a.Severity, &a.Type)
		if err != nil {
			continue
		}
		anomalies = append(anomalies, a)
	}
	return anomalies, nil
}

func GetAnomaliesHistory(days int) ([]Anomaly, error) {
	query := `SELECT id, timestamp, metric, value, threshold, severity, type
		FROM anomalies 
		WHERE timestamp > datetime('now', '-' || ? || ' days')
		ORDER BY timestamp DESC`

	rows, err := db.Query(query, days)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var anomalies []Anomaly
	for rows.Next() {
		var a Anomaly
		err := rows.Scan(&a.ID, &a.Timestamp, &a.Metric, &a.Value, &a.Threshold, &a.Severity, &a.Type)
		if err != nil {
			continue
		}
		anomalies = append(anomalies, a)
	}
	return anomalies, nil
}

func GetBaselineStats() (map[string]map[string]float64, error) {
	stats := make(map[string]map[string]float64)

	metrics := []string{"cpu_usage", "ram_usage", "gpu_usage"}
	for _, metric := range metrics {
		colName := metric + "_mean"
		var mean, std, threshold float64

		query := `SELECT AVG(` + colName + `), STDDEV(` + colName + `), AVG(` + colName + `) + 2 * STDDEV(` + colName + `)
			FROM features WHERE ` + colName + ` IS NOT NULL`

		row := db.QueryRow(query)
		err := row.Scan(&mean, &std, &threshold)
		if err != nil {
			continue
		}

		stats[metric] = map[string]float64{
			"mean":      mean,
			"std":       std,
			"threshold": threshold,
		}
	}
	return stats, nil
}

type IngestPayload struct {
	Timestamp string  `json:"timestamp"`
	CPUUsage  float64 `json:"cpu_usage"`
	CPUtemp   float64 `json:"cpu_temp"`
	RAMUsage  float64 `json:"ram_usage"`
	RAMTotal  float64 `json:"ram_total"`
	RAMUsed   float64 `json:"ram_used"`
	DiskRead  float64 `json:"disk_read"`
	DiskWrite float64 `json:"disk_write"`
	NetSent   float64 `json:"network_sent"`
	NetRecv   float64 `json:"network_recv"`
	GPUUsage  float64 `json:"gpu_usage"`
	GPUtemp   float64 `json:"gpu_temp"`
}

func InsertMetrics(payload *IngestPayload) error {
	timestamp, err := time.Parse(time.RFC3339, payload.Timestamp)
	if err != nil {
		timestamp = time.Now()
	}

	query := `INSERT INTO raw_metrics 
		(timestamp, cpu_usage, cpu_temp, ram_usage, ram_total, ram_used, disk_usage, disk_read, disk_write,
		net_sent, net_recv, gpu_usage, gpu_temp, processed)
		VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 0, 0)`

	_, err = db.Exec(query,
		timestamp,
		payload.CPUUsage,
		payload.CPUtemp,
		payload.RAMUsage,
		payload.RAMTotal,
		payload.RAMUsed,
		payload.DiskRead,
		payload.DiskWrite,
		payload.NetSent,
		payload.NetRecv,
		payload.GPUUsage,
		payload.GPUtemp,
	)

	if err != nil {
		log.Printf("Error inserting metrics: %v", err)
		return err
	}

	log.Printf("Metrics inserted: CPU %.1f%%, RAM %.1f%%", payload.CPUUsage, payload.RAMUsage)
	return nil
}
