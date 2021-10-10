package main

import (
	"archive/zip"
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/feature/s3/manager"
	"github.com/aws/aws-sdk-go-v2/service/codepipeline"
	"github.com/aws/aws-sdk-go-v2/service/codepipeline/types"
	"github.com/aws/aws-sdk-go-v2/service/s3"

	// "github.com/aws/aws-sdk-go-v2/session"
	// "github.com/aws/aws-sdk-go-v2/feature/rds/auth"
	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/mysql"
	_ "github.com/golang-migrate/migrate/v4/source/file"
	"github.com/spf13/viper"
)

type DB struct {
  name string
  username string
  password string
  host string
  port string
}

func Unzip(src, dest string) error {
    r, err := zip.OpenReader(src)
    if err != nil {
        return err
    }
    defer func() {
        if err := r.Close(); err != nil {
            panic(err)
        }
    }()

    os.MkdirAll(dest, 0755)

    extractAndWriteFile := func(f *zip.File) error {
        rc, err := f.Open()
        if err != nil {
            return err
        }
        defer func() {
            if err := rc.Close(); err != nil {
                panic(err)
            }
        }()

        path := filepath.Join(dest, f.Name)

        if !strings.HasPrefix(path, filepath.Clean(dest) + string(os.PathSeparator)) {
            return fmt.Errorf("illegal file path: %s", path)
        }

        if f.FileInfo().IsDir() {
            os.MkdirAll(path, f.Mode())
        } else {
            os.MkdirAll(filepath.Dir(path), f.Mode())
            f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
            if err != nil {
                return err
            }
            defer func() {
                if err := f.Close(); err != nil {
                    panic(err)
                }
            }()

            _, err = io.Copy(f, rc)
            if err != nil {
                return err
            }
        }
        return nil
    }

    for _, f := range r.File {
        err := extractAndWriteFile(f)
        if err != nil {
            return err
        }
    }

    return nil
}

func handler(ctx context.Context, event events.CodePipelineJobEvent) {
  viper.SetConfigType("env")
  viper.SetConfigFile(".env")
  viper.AutomaticEnv()
  if err := viper.ReadInConfig(); err != nil {
    if _, ok := err.(viper.ConfigFileNotFoundError); ok {
      log.Println("Config file not found")
    } else {
      log.Println(err)
    }
  }

  cfg, err := config.LoadDefaultConfig(ctx)
  if err != nil {
    panic("configuration error: " + err.Error())
  }

  jobId := event.CodePipelineJob.ID
  inputArtifacts := event.CodePipelineJob.Data.InputArtifacts
  downloader := manager.NewDownloader(s3.NewFromConfig(cfg))
  file, err := os.Create("/tmp/SourceArtifact")
  if err != nil {
      log.Println(err)
  }
  defer file.Close()
  for i := 0;i < len(inputArtifacts); i += 1 {
    if inputArtifacts[i].Name == "SourceArtifact" {
      _, err := downloader.Download(ctx, file,
        &s3.GetObjectInput{
            Bucket: aws.String(inputArtifacts[i].Location.S3Location.BucketName),
            Key:    aws.String(inputArtifacts[i].Location.S3Location.ObjectKey),
      })
      if err != nil {
          fmt.Println(err)
      }
    }
  }

  log.Println("Unzipping SourceArtifact")
  unzipLocation := "/tmp/sec-app"
  err = Unzip(file.Name(), unzipLocation)
  if err != nil {
    log.Println(err)
  }

  // files, err := ioutil.ReadDir("/tmp/sec-app/migrations")
  // if err != nil {
  //   log.Println(err)
  // }
  // for _, f := range files {
  //   log.Println(f.Name())
  // }

  // TODO: iam db auth currently using the default user
  // authenticationToken, err := auth.BuildAuthToken(
  //   ctx,
  //   fmt.Sprintf("%s:%s", viper.Get("db_host").(string), "3306"),
  //   "us-east-2",
  //   "migrationsLambda",
  //   cfg.Credentials,
  // )
  // if err != nil {
  //   panic("failed to create authentication token: " + err.Error())
  // }

  db := DB {
    name: viper.GetString("db_name"),
    username: viper.GetString("db_user"),
    host: viper.GetString("db_host"),
    port: viper.GetString("db_port"),
    password: viper.GetString("db_pass"),
  }

  dsn := fmt.Sprintf(
    "mysql://%s:%s@tcp(%s:%s)/%s",
    db.username, db.password, db.host, db.port, db.name,
  )

  codepipelineClient := codepipeline.NewFromConfig(cfg)
  failureDetails :=  types.FailureDetails {
    Message: aws.String("Error completing migration"),
    Type: types.FailureTypeJobFailed,
  }

  log.Println("Running migration")
  fileString := fmt.Sprintf("file://%s", filepath.Join(unzipLocation, "migrations"))
  m, err := migrate.New(fileString, dsn)
  if err != nil {
    log.Println(err.Error())
    log.Println("Sending unsuccessful job to Codepipeline")
    failedInput := codepipeline.PutJobFailureResultInput{ JobId: aws.String(jobId), FailureDetails: &failureDetails }
    codepipelineClient.PutJobFailureResult(ctx, &failedInput)
    return
  }

  if err := m.Up(); err != nil {
    if err.Error() == "no change" {
      log.Println(err)
    } else {
      log.Println(err.Error())
      log.Println("Sending unsuccessful job to Codepipeline")
      failedInput := codepipeline.PutJobFailureResultInput{ JobId: &jobId, FailureDetails: &failureDetails }
      codepipelineClient.PutJobFailureResult(ctx, &failedInput)
      return
    }
  }

  log.Println("Sending successful job to Codepipeline")
  successInput := codepipeline.PutJobSuccessResultInput{ JobId: &jobId }
  codepipelineClient.PutJobSuccessResult(ctx, &successInput)
}

func main() {
  lambda.Start(handler)
}
