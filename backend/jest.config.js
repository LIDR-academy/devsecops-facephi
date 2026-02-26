module.exports = {
    preset: 'ts-jest',
    testEnvironment: 'node',
    coverageReporters: ['lcov', 'text'],
    coverageDirectory: 'coverage',
    collectCoverageFrom: [
        'src/**/*.ts',
        '!src/**/*.d.ts',
        '!src/**/*.test.ts',
    ],
};