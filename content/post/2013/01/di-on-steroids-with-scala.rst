Dependency Injection on steroids with Scala : Value injection on traits
#######################################################################
:date: 2013-01-15
:tags: scala, software design, dependency injection
:category: post
:slug: post/di-on-steroids-with-scala-value-injection-on-traits

Introduction
------------
This text presents the concept and characteristics of **value injection on traits** which is a Dependency Injection (DI)
variant in Scala which I have been using lately instead of the
`cake pattern <http://jonasboner.com/2008/10/06/real-world-scala-dependency-injection-di/>`_ and the
`DI variants that Martin Fowler introduced <http://www.martinfowler.com/articles/injection.html>`_.

I hope to clarify the elegance of this pattern and why it works so well with Scala, both for structuring the code and doing the wiring.

The cake pattern has worked for me in the past, but on larger codebases I am encountering issues with it.
I am not going into the details of these issues here, 
but if you are interested Adam Warski has a `nice post <http://www.warski.org/blog/2011/04/di-in-scala-cake-pattern-pros-cons/>`_ on this,
which matches well with my experiences.
Instead, I wanted to keep this text fairly minimal and focus on introducing the idea of **value injection on traits**.

Before starting off, note that DI has 2 parts:

* **wirability** (or - to stay closer to the term DI - injectability) - this part has become the meta-pattern of OO programming.
  I now think of it as almost synonymous with *good software design*, or at least a necessary precondition for a good design.
  In this text I will refer to this code as **wirable code**.
* **wiring** (or - you got it, doesn't sound nice, but unfortunately reality demands it - injecting) -
  in Java the wiring is typically done with a DI container/framework such as Spring or Guice, but that's just an option: 
  the good software design meta-pattern comes with freedom of choice.
  I will take advantage of this freedom and use Scala for writing **wiring code** (and wiring actually becomes fun!).

I will start with a short introduction of the pattern using a simple example.
This is just meant to give some basic intuition on the pattern.
In the two sections after that, I will give a more in depth presentation of the wirable and wiring code respectively, while also giving some more realistic examples.
And I will end with the conclusions.

Value injection on traits
-------------------------
The name of the pattern "Value injection on traits" is analogous to the terminology that Martin Fowler introduced.
I have added *on traits* to *value injection* to make the contrast with classes explicit.
You *can* do value injection on classes, but that looks a lot like the constructor injection pattern that we already know.

This is how the "Value injection on traits" pattern looks like, using the movie example of Fowler
(or if you prefer the `Warmer example that Jonas Boner introduced <|filename|/post/2013/01/warmer-example-using-value-injection.md>`_):

.. code-block:: none

  trait MovieFinder {
    def findAll:Seq[Movie]
  }

  // this is the trait where it is all about i.e. the reason that the pattern is called value injection on *traits*
  trait MovieLister {
    //the important *value* in the pattern with 'finder' being the *injectable*
    val finder: MovieFinder

    def listAll: Unit = println(finder.findAll.mkString("/n"))
  }

  class ColonMovieFinder(filename: String) extends MovieFinder {
    override def findAll:Seq[Movie] = ??? //left as exercise for the bored reader
  }

Although contrived in this simple example, the key is that :code:`MovieLister` can be a **trait** (apart from a :code:`class`) while
nicely **separating concerns** by using a :code:`val` to access the functionality of :code:`MovieFinder`.

**Note** (thanks Naftoli for your comment):
when used in e.g. the cake pattern, abstract values are usually a source of :code:`NullPointerException`'s and you will
have to workaround it by using :code:`lazy val`'s (and even then it can get tricky).
This happens since you don't have any control over when a :code:`val` is instantiated.
When you use this pattern though, since the concerns are separated, you *can* control it and you don't have
to worry about :code:`NullPointerException`'s and resort to :code:`lazy val`'s.

The next section will show more interesting characteristics of the wirable code.

The wiring code can then be as simple as this (so simple that you can hardly call it wiring):

.. code-block:: none

  val myLister = new MovieLister {
    finder = new ColonMovieFinder("someFile.txt")
  }

The section *structure of wiring code* has an example that shows the general structure.

Structure of wirable code
-------------------------
The wirable code of the :code:`MovieLister` example was just enough to explain the pattern and its name.
What is less clear from that example is that there is an interesting recursive pattern behind this form of DI (which makes DI 'go round').

This **recursive pattern** typically has this form:

* **base trait** - at its core usually a simple trait with a small number of (typically 1) **abstract methods**
* **extension of base trait** - at its core usually containing:
    * a small number of **abstract injectable values**; and
    * an **implementation of the abstract method** that is defined in the base trait

What makes this structure **recursive** is that the types of the abstract injectable values are typically **base traits** again.

Here's an annotated example from the :code:`authentication` object of `io.svc.security <https://github.com/svc-io/io.svc.security>`_
(which is a security framework that I have created and uses the pattern all-over):

.. code-block:: none

  // *base trait*
  trait InputValidator[-I, +U, +F] {
    // *abstract method*
    def validateInput(in: I): Validation[F, U]
  }

  // *extension of base trait*
  trait CredentialsInputValidator[In, Credentials, User, +F] extends InputValidator[In, User, F] {

    // *abstract, injectable value(s); typed as a base trait*
    val credentialsExtractor: CredentialsExtractor[In, Credentials, F]
    val authService: AuthenticationService[Credentials, User, F]

    // *definition of the method that was declared in base trait, using the abstract values*
    override def validateInput(in: In): Validation[F, User] = {
      credentialsExtractor.extract(in) flatMap authService.authenticate
    }
  }


Structure of wiring code
------------------------

In essence, the wiring code comes down to building a **tree** -
another **recursive structure** - which is constructed using the 'wirable' building blocks.

I will show you how I have used it in `io.svc.security.play.demo <https://github.com/svc-io/io.svc.security.play.demo>`_ -
a play2 demo app for `io.svc.security.play <https://github.com/svc-io/io.svc.security.play>`_
(:code:`io.svc.security.play` is a play 2 binding of :code:`io.svc.security`).

Here's an extract:

.. code-block:: none

  trait DemoBasicAuth[A] extends PlayAuth[A, DemoUser] {
    val inputValidator = new CredentialsInputValidator[Request[A], UsernamePasswordCredentials,
                                                       DemoUser, AuthenticationFailure] {
      val credentialsExtractor = new PlayBasicAuthenticationCredentialsExtractor[A]
      val authService = demoSecurity.demoAuthService
    }
    val authFailureHandler = playAuthentication.authFailureHandler[A](
                               demoSecurity.unauthorizedHtml.withHeaders(("WWW-Authenticate", "Basic realm=\"Demo\"")))
  }

  trait DemoBasicAuthSecurity[A] extends PlaySecurity[A, DemoUser] {
    val auth = new DemoBasicAuth[A] {}
  }


So, in this way, wiring becomes like building a **flexible tree** using a syntax that nicely shows the **structure of the tree**.

It's flexible in the sense that parts of the tree can be constructed **inline** (like the :code:`inputValidator` in :code:`DemoBasicAuth`),
while it is just as easy to **reuse** definitions that are made elsewhere. For example:

* reusing a :code:`val`: :code:`val authService = demoSecurity.demoAuthService`
* applying a :code:`def`: :code:`val authFailureHandler` calls the generic function :code:`playAuthentication.authFailureHandler` to instantiate a specific :code:`AuthFailureHandler`).
* reusing a :code:`trait`: :code:`val auth = new DemoBasicAuth[A] {}`

It is also flexible in the sense that the structure of each subtree is determined by the **choice of the extension of the base trait for that subtree**.
E.g. choosing :code:`CredentialsInputValidator` as :code:`inputValidator` implies that :code:`credentialsExtractor` and :code:`authService` need to be assigned on the next level,
but any other :code:`InputValidator` can take its place defining its own subtree structure,
including a dummy :code:`InputValidator` like this which defines :code:`InputValidator`'s abstract method on the fly (atypical for the pattern) and has no :code:`val`'s on the next level:

.. code-block:: none

  val inputValidator = new InputValidator[Request[A], DemoUser, AuthenticationFailure] {
    def validateInput(in: Request[A]) = Success(DemoUser("joe", "password4joe"))
  }

In the former example I have chosen to reuse :code:`DemoBasicAuth` and :code:`demoSecurity.demoAuthService`.
But is also interesting to inline them and see how a larger tree looks like:

.. code-block:: none

  trait DemoBasicAuthSecurity[A] extends PlaySecurity[A, DemoUser] {
    val auth = new PlayAuth[A, DemoUser] {
      val inputValidator = new CredentialsInputValidator[Request[A], UsernamePasswordCredentials,
                                                         DemoUser, AuthenticationFailure] {
        val credentialsExtractor = new PlayBasicAuthenticationCredentialsExtractor[A]
        val authService = new UsernamePasswordCredentialsAuthenticationService[DemoUser] {
          val userService = demoSecurity.demoUserService
          val credentialsValidator = demoSecurity.demoCredentialsValidator
        }
      }
      val authFailureHandler = playAuthentication.authFailureHandler[A](
                                demoSecurity.unauthorizedHtml.withHeaders(("WWW-Authenticate", "Basic realm=\"Demo\"")))
    }
  }

Conclusion
----------
This pattern certainly changed *my* way of programming in Scala. There are a couple of things I like about it.

One is that it **maps great to the core DI concepts** that I already know (and are good in my eyes), which makes the code **intuitive to write and read**.

It is also concise in the sense that both the wirable and the wiring code are **free of biolerplate**.
E.g. you don't have to make any alterations or additions to the code just for the sake of making the code properly wirable
(as opposed to the cake pattern e.g. where the code is wrapped in a Component and you have to use :code:`lazy val`'s among others).

Another thing I like is the way it takes advantage of the Scala language, e.g. the fact that the pattern also **works on traits**.
This makes applying DI very powerful and flexible.

Also the **wiring code** is able to take full advantage of the Scala language: **no DI container/framework/library is required**,
and its **building blocks can be reused in a powerful, minimalistic (Scalaistic) way**.
And finally I like how the **structure of the wiring** is immediately visible.

I hope it will be of value to you too. 
Suggestions, ideas and thoughts are welcome!

.. class:: well

About me
--------

This is one of the interesting things that I learned on my software development ride,
which started last year after quitting my job in Amsterdam and migrating from the Netherlands to Edinburgh, Scotland.

I took this move as an opportunity to focus full-time on developing myself in the direction of my fascinations & passions (believe driven development ;)).
Programming languages is one of my passions and learning more Scala was (and is) one of my goals.

I took `webservices.io <https://webservices.io>`_ as the vehicle of the ride and - apart from learning more Scala -
here is what I made, in order of coolness (by my definition of coolness, that is):

1. **Backend** of webservices.io (using Scala with Play2): pluggable service architecture, e.g. the services can be nicely composed.
   Still lots of ideas here (keep you posted).
2. In the **DevOps** area (using Python):
   flexible infrastructure architecture that enables to quickly switch cloud providers or move to a non-cloud setup.
   Also gained more experience with multiple cloud services (mainly AWS on IAAS level, but also several PAAS solutions);
3. **Website** (using Play2 and twitter bootstrap): this, among others, resulted in the first webdesign of which I am not unproud.

I will soon be reaching the point where I cannot work full-time/speed on `webservices.io <https://webservices.io>`_ anymore,
although I will certainly work further on it - with a lower speed - in my spare time.
Also I am open for & interested in ideas to keep this project going at various levels of speed.

Anyway, this has been a great experience.

In the future I would really like to continue working in this area - with *this area* being loosely defined as:

* **Software development and architecture** - I have mostly been working in the role of software developer and architect,
  but I also enjoy working on other parts of the software lifecycle
  ranging from brainstorming new ideas and analyzing requirements to testing.

* **JVM platform** - My favorite platform. I have experience with the following languages:

  * **Scala** - I think Scala has a great future ahead with powers that go way beyond Java
  * **Java** - I have been working with Java for more than 10 years; still interested in Java projects
  * **Groovy** - I have worked on some Groovy/Grails projects in the past and found it also a pleasure to work with

* **Cloud computing**

  * Development and architecture for cloud-based applications
  * Migrating applications and services to the cloud
  * DevOps work

* **Environment** - I feel at home in agile environment with e.g. start ups,
  but also with enterprises as long as there is a culture of looking forward and to *improve* software.

.. role:: raw-role(raw)
   :format: html

If I can be of help to you in one of these areas,
please get in touch via `twitter <http://twitter.com/rintcius>`_ or :raw-role:`<span><script language="JavaScript"> var name = "rintcius"; var domain = "gmai" + "l.c" + "om"; document.write('<a href="mai' + 'lto:' + name + '@' + domain + '">'); document.write('email' + '</a>');  </script> </span>`.
