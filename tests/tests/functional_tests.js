"use strict";

var expect = require("chai").expect;
var sinon = require("sinon");
var randomBytes = require("crypto").randomBytes;

var ws = require('ws');

var BEARER_TOKEN = "13cbb5664aaccd662d803e71e547cdb58485ce25477f635bc5051aa550eed00d";

describe('websockets', function() {
  var gecko, client;

  beforeEach(function(done) {
    // Connects the Gecko
    gecko = new ws("ws://localhost:8765/worker");
    gecko.on('close', function() {
      gecko.isClosed = true;
    });
    gecko.on('open', function() {
      // Send the Gecko Hello
      gecko.send(JSON.stringify({
        "messageType": "hello",
        "action": "worker-hello",
        "geckoId": "gecko-1243"
      }));
    });

    // Connects the client
    client = new ws("ws://localhost:8765/");
    client.on('close', function() {
      client.isClosed = true;
    });
    client.on('open', done);
  });

  afterEach(function(done) {
    client.close();
    gecko.close();
    done();
  });

  it("should send the client offer through to the Gecko server", function(done) {
    client.send(JSON.stringify({
      "messageType": "hello",
      "action": "client-hello",
      "authorization": "Bearer " + BEARER_TOKEN,
      "source": "http://localhost:8080/worker.js",
      "webrtcOffer": "<sdp-offer>"
    }));

    gecko.on("message", function(data) {
      var message = JSON.parse(data);
      expect(message.messageType).to.eql("new-worker");
      expect(message.userId).to.not.eql(undefined);
      expect(message.source).to.eql("http://localhost:8080/worker.js");
      expect(message.webrtcOffer).to.eql("<sdp-offer>");
      done();
    });
  });

  it("should send back the gecko answer to the client");
  it("should send back the gecko error answer to the client");
  it("should send ICE candidate from client to server");
  it("should send ICE candidate from server to client");

  it("should always send clients offer to the same gecko for the same uid");

});
