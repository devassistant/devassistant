package org.PROJECT_NAME.launcher;

import java.net.URL;
import java.security.ProtectionDomain;

import org.eclipse.jetty.server.Connector;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.ServerConnector;
import org.eclipse.jetty.webapp.WebAppContext;

public class Start {
	public static void main(String[] args) throws Exception {
		Server server = new Server();

		int port = Integer.getInteger("jetty.port", 8080).intValue();
		ServerConnector connector = new ServerConnector( server );
		connector.setPort(port);
		server.setConnectors(new Connector[] { connector });

		WebAppContext webapp = new WebAppContext();
		webapp.setContextPath("/");

		ProtectionDomain protectionDomain = Start.class.getProtectionDomain();
		URL location = protectionDomain.getCodeSource().getLocation();
		webapp.setWar(location.toExternalForm());

		server.setHandler(webapp);

		server.start();

		System.out.println("done.");
		System.out.println("Successfully deployed: http://localhost:" + port + "/");
		System.out.println("Press any key to stop the server...");

		System.in.read();
		server.stop();
		server.join();
	}
}
