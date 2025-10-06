import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { CoreStack } from '../lib/stacks/core-stack';
import { ApiStack } from '../lib/stacks/api-stack';
import { WebStack } from '../lib/stacks/web-stack';
import { MonitoringStack } from '../lib/stacks/monitoring-stack';

describe('Infrastructure Stacks', () => {
  let app: cdk.App;
  let coreStack: CoreStack;

  beforeEach(() => {
    app = new cdk.App();
    coreStack = new CoreStack(app, 'TestCoreStack');
  });

  test('CoreStack can be created', () => {
    const template = Template.fromStack(coreStack);
    // Basic test to ensure stack can be synthesized
    expect(template).toBeDefined();
  });

  test('ApiStack can be created with CoreStack dependency', () => {
    const apiStack = new ApiStack(app, 'TestApiStack', {
      coreStack: coreStack
    });
    
    const template = Template.fromStack(apiStack);
    expect(template).toBeDefined();
  });

  test('WebStack can be created with ApiStack dependency', () => {
    const apiStack = new ApiStack(app, 'TestApiStack', {
      coreStack: coreStack
    });
    
    const webStack = new WebStack(app, 'TestWebStack', {
      apiStack: apiStack
    });
    
    const template = Template.fromStack(webStack);
    expect(template).toBeDefined();
  });

  test('MonitoringStack can be created with all dependencies', () => {
    const apiStack = new ApiStack(app, 'TestApiStack', {
      coreStack: coreStack
    });
    
    const webStack = new WebStack(app, 'TestWebStack', {
      apiStack: apiStack
    });
    
    const monitoringStack = new MonitoringStack(app, 'TestMonitoringStack', {
      coreStack: coreStack,
      apiStack: apiStack,
      webStack: webStack
    });
    
    const template = Template.fromStack(monitoringStack);
    expect(template).toBeDefined();
  });
});