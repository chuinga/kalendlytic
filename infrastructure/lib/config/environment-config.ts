import * as fs from 'fs';
import * as path from 'path';

export interface EnvironmentConfig {
  environment: string;
  region: string;
  account: string;
  stackPrefix: string;
  tags: Record<string, string>;
  core: CoreConfig;
  api: ApiConfig;
  web: WebConfig;
  monitoring: MonitoringConfig;
  security: SecurityConfig;
  backup?: BackupConfig;
  disaster_recovery?: DisasterRecoveryConfig;
}

export interface CoreConfig {
  dynamodb: {
    billingMode: 'PAY_PER_REQUEST' | 'PROVISIONED';
    readCapacity?: number;
    writeCapacity?: number;
    autoScaling?: {
      enabled: boolean;
      minCapacity: number;
      maxCapacity: number;
      targetUtilization: number;
    };
    pointInTimeRecovery: boolean;
    backupRetention: number;
    deletionProtection: boolean;
  };
  cognito: {
    passwordPolicy: {
      minimumLength: number;
      requireUppercase: boolean;
      requireLowercase: boolean;
      requireNumbers: boolean;
      requireSymbols: boolean;
    };
    mfaConfiguration: 'OFF' | 'OPTIONAL' | 'REQUIRED';
    selfSignUpEnabled: boolean;
    emailVerificationRequired: boolean;
    advancedSecurityMode?: 'OFF' | 'AUDIT' | 'ENFORCED';
  };
  kms: {
    keyRotation: boolean;
    deletionWindow: number;
    multiRegion?: boolean;
  };
  secrets: {
    automaticRotation: boolean;
    rotationInterval?: number;
    crossRegionReplication?: boolean;
  };
}

export interface ApiConfig {
  lambda: {
    runtime: string;
    timeout: number;
    memorySize: number;
    reservedConcurrency: number;
    environment: Record<string, string>;
    deadLetterQueue?: {
      enabled: boolean;
      maxReceiveCount: number;
    };
  };
  apiGateway: {
    throttling: {
      rateLimit: number;
      burstLimit: number;
    };
    cors: {
      allowOrigins: string[];
      allowMethods: string[];
      allowHeaders: string[];
    };
    caching?: {
      enabled: boolean;
      ttl: number;
      clusterSize: string;
    };
  };
  eventBridge: {
    retentionDays: number;
  };
}

export interface WebConfig {
  s3: {
    versioning: boolean;
    encryption: string;
    publicReadAccess: boolean;
    blockPublicAccess: boolean;
    crossRegionReplication?: {
      enabled: boolean;
      destinationBucket: string;
    };
  };
  cloudFront: {
    priceClass: string;
    cachingEnabled: boolean;
    compressionEnabled: boolean;
    customDomain: {
      enabled: boolean;
      domainName: string;
      certificateArn: string;
    };
    waf?: {
      enabled: boolean;
      webAclArn: string;
    };
  };
}

export interface MonitoringConfig {
  cloudWatch: {
    logRetention: number;
    metricsEnabled: boolean;
    detailedMonitoring: boolean;
    customMetrics?: boolean;
  };
  alarms: {
    enabled: boolean;
    snsNotifications: boolean;
    emailEndpoints: string[];
    slackWebhook?: string;
  };
  xray: {
    enabled: boolean;
    samplingRate: number;
  };
  dashboard?: {
    enabled: boolean;
    widgets: string[];
  };
}

export interface SecurityConfig {
  waf: {
    enabled: boolean;
    rules?: string[];
    rateLimiting?: {
      enabled: boolean;
      limit: number;
    };
  };
  vpc: {
    enabled: boolean;
    cidr?: string;
    availabilityZones?: number;
    natGateways?: number;
  };
  guardDuty?: {
    enabled: boolean;
  };
  config?: {
    enabled: boolean;
  };
}

export interface BackupConfig {
  enabled: boolean;
  schedule: string;
  retentionDays: number;
  crossRegionCopy: boolean;
}

export interface DisasterRecoveryConfig {
  enabled: boolean;
  secondaryRegion: string;
  rto: number; // Recovery Time Objective in hours
  rpo: number; // Recovery Point Objective in hours
}

export class EnvironmentConfigLoader {
  private static instance: EnvironmentConfigLoader;
  private configCache: Map<string, EnvironmentConfig> = new Map();

  public static getInstance(): EnvironmentConfigLoader {
    if (!EnvironmentConfigLoader.instance) {
      EnvironmentConfigLoader.instance = new EnvironmentConfigLoader();
    }
    return EnvironmentConfigLoader.instance;
  }

  public loadConfig(environment: string): EnvironmentConfig {
    // Check cache first
    if (this.configCache.has(environment)) {
      return this.configCache.get(environment)!;
    }

    // Load from file
    const configPath = path.join(__dirname, '../../config/environments', `${environment}.json`);
    
    if (!fs.existsSync(configPath)) {
      throw new Error(`Environment configuration not found: ${configPath}`);
    }

    try {
      const configContent = fs.readFileSync(configPath, 'utf-8');
      const config: EnvironmentConfig = JSON.parse(configContent);
      
      // Validate required fields
      this.validateConfig(config);
      
      // Process environment variables in config
      const processedConfig = this.processEnvironmentVariables(config);
      
      // Cache the config
      this.configCache.set(environment, processedConfig);
      
      return processedConfig;
    } catch (error) {
      throw new Error(`Failed to load environment configuration for ${environment}: ${error}`);
    }
  }

  private validateConfig(config: EnvironmentConfig): void {
    const requiredFields = ['environment', 'region', 'stackPrefix', 'core', 'api', 'web', 'monitoring', 'security'];
    
    for (const field of requiredFields) {
      if (!(field in config)) {
        throw new Error(`Missing required configuration field: ${field}`);
      }
    }
  }

  private processEnvironmentVariables(config: EnvironmentConfig): EnvironmentConfig {
    const configStr = JSON.stringify(config);
    const processedStr = configStr.replace(/\$\{([^}]+)\}/g, (match, envVar) => {
      const value = process.env[envVar];
      if (value === undefined) {
        throw new Error(`Environment variable ${envVar} is not defined`);
      }
      return value;
    });
    
    return JSON.parse(processedStr);
  }

  public getAvailableEnvironments(): string[] {
    const configDir = path.join(__dirname, '../../config/environments');
    
    if (!fs.existsSync(configDir)) {
      return [];
    }

    return fs.readdirSync(configDir)
      .filter(file => file.endsWith('.json'))
      .map(file => path.basename(file, '.json'));
  }

  public clearCache(): void {
    this.configCache.clear();
  }
}